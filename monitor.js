#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvFile(path.join(__dirname, '.env'));

const targets = [
  { name: process.env.TARGET_TEST_NAME ?? 'Mescladís Test', url: process.env.TARGET_TEST_URL ?? '' },
  { name: process.env.TARGET_1_NAME ?? 'Mescladís 1', url: process.env.TARGET_1_URL ?? '' },
  { name: process.env.TARGET_2_NAME ?? 'Mescladís 2', url: process.env.TARGET_2_URL ?? '' },
  { name: process.env.TARGET_3_NAME ?? 'Mescladís 3', url: process.env.TARGET_3_URL ?? '' },
  { name: process.env.TARGET_4_NAME ?? 'Mescladís 4', url: process.env.TARGET_4_URL ?? '' },
  { name: process.env.TARGET_5_NAME ?? 'Mescladís 5', url: process.env.TARGET_5_URL ?? '' },
  { name: process.env.TARGET_6_NAME ?? 'Mescladís 6', url: process.env.TARGET_6_URL ?? '' },
  { name: process.env.TARGET_7_NAME ?? 'Mescladís 7', url: process.env.TARGET_7_URL ?? '' },
  { name: process.env.TARGET_8_NAME ?? 'Mescladís 8', url: process.env.TARGET_8_URL ?? '' },
  { name: process.env.TARGET_9_NAME ?? 'Mescladís 9', url: process.env.TARGET_9_URL ?? '' },
  { name: process.env.TARGET_10_NAME ?? 'Mescladís 10', url: process.env.TARGET_10_URL ?? '' },
  { name: process.env.TARGET_11_NAME ?? 'Mescladís 11', url: process.env.TARGET_11_URL ?? '' },
];

const POLL_INTERVAL_MS = readInteger('POLL_INTERVAL_MS', 60_000);
const PEAK_POLL_INTERVAL_MS = readInteger('PEAK_POLL_INTERVAL_MS', 30_000);
const PEAK_START_HOUR = readInteger('PEAK_START_HOUR', 8);
const PEAK_END_HOUR = readInteger('PEAK_END_HOUR', 21);
const MONITOR_LANE_INTERVAL_MS = readInteger('MONITOR_LANE_INTERVAL_MS', 30_000);
const MONITOR_LANE_START_OFFSETS_MS = parseOffsetList(
  process.env.MONITOR_LANE_START_OFFSETS_MS ?? '0,10000,30000',
);
const MONITOR_TIMEZONE = process.env.MONITOR_TIMEZONE ?? 'Europe/Madrid';
const SLOT_TIMEZONE = process.env.SLOT_TIMEZONE ?? 'Europe/Madrid';
const ERROR_CONFIRMATION_ROUNDS = readInteger('MONITOR_ERROR_CONFIRMATION_ROUNDS', 2);
const ERROR_NOTIFICATION_COOLDOWN_MS = readInteger('MONITOR_ERROR_NOTIFICATION_COOLDOWN_MS', 600_000);
const ERROR_BURST_TARGET_THRESHOLD = readInteger('MONITOR_ERROR_BURST_TARGET_THRESHOLD', 3);
const MONITOR_START_DATE = process.env.MONITOR_START_DATE ?? '2026-04-22';
const MONITOR_END_DATE = process.env.MONITOR_END_DATE ?? '2026-06-15';
const PAGE_TIMEOUT_MS = readInteger('PAGE_TIMEOUT_MS', 45_000);
const PAGE_GOTO_DELAY_MS = readInteger('PAGE_GOTO_DELAY_MS', 500);
const QCLAW_WEBHOOK_URL = (process.env.QCLAW_WEBHOOK_URL ?? '').trim();
const QCLAW_WEBHOOK_SECRET = (process.env.QCLAW_WEBHOOK_SECRET ?? '').trim();
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const ALERT_FILE_PATH = (process.env.ALERT_FILE_PATH ?? '').trim();
const MONITOR_HEARTBEAT_FILE_PATH = (process.env.MONITOR_HEARTBEAT_FILE_PATH ?? path.join(__dirname, 'monitor_heartbeat.json')).trim();
const STATE_FILE = path.join(__dirname, process.env.STATE_FILE ?? 'state.json');
const HEADLESS = (process.env.HEADLESS ?? 'true').toLowerCase() !== 'false';
const monitorStartedAt = new Date().toISOString();

const stopSignals = new Set();
let browser = null;
let heartbeatPulseTimer = null;
let latestHeartbeatDetails = {
  phase: 'startup',
  roundId: 0,
  laneId: null,
  laneName: 'startup',
  laneOffsetMs: 0,
  laneIntervalMs: MONITOR_LANE_INTERVAL_MS,
  laneTargetCount: targets.length,
  nextPollIntervalMs: MONITOR_LANE_INTERVAL_MS,
};
const targetPages = new Map();
const targetProbeLocks = new Map();
const targetStateLocks = new Map();
let activeErrorIncident = null;

process.on('SIGINT', () => {
  stopSignals.add('SIGINT');
});

process.on('SIGTERM', () => {
  stopSignals.add('SIGTERM');
});

async function main() {
  validateTargets(targets);
  const snapshots = new Map(Object.entries(loadState().targets ?? {}));
  const lanes = buildMonitorLanes(targets);

  await seedAlertFile();
  await writeMonitorHeartbeat({
    phase: 'startup',
    roundId: 0,
    laneId: null,
    laneName: 'startup',
    laneOffsetMs: 0,
    laneIntervalMs: MONITOR_LANE_INTERVAL_MS,
    laneTargetCount: targets.length,
    nextPollIntervalMs: MONITOR_LANE_INTERVAL_MS,
  });

  browser = await chromium.launch({ headless: HEADLESS });
  heartbeatPulseTimer = setInterval(() => {
    writeMonitorHeartbeat(latestHeartbeatDetails).catch(() => {});
  }, 30_000);

  try {
    await Promise.all(lanes.map((lane) => runLane(lane, snapshots)));
  } finally {
    if (heartbeatPulseTimer) {
      clearInterval(heartbeatPulseTimer);
      heartbeatPulseTimer = null;
    }

    await writeMonitorHeartbeat({
      phase: 'stopping',
      roundId: null,
      laneId: null,
      laneName: 'stopping',
      laneOffsetMs: null,
      laneIntervalMs: null,
      laneTargetCount: targets.length,
      nextPollIntervalMs: null,
    });

    for (const page of targetPages.values()) {
      await page.close().catch(() => {});
    }
    targetPages.clear();

    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function runLane(lane, snapshots) {
  if (lane.offsetMs > 0) {
    console.log(`[LANE] ${lane.name} initial delay ${lane.offsetMs}ms`);
    await sleep(lane.offsetMs);
  }

  let round = 0;
  while (!stopSignals.size) {
    round += 1;
    latestHeartbeatDetails = {
      phase: 'round_start',
      roundId: round,
      laneId: lane.id,
      laneName: lane.name,
      laneOffsetMs: lane.offsetMs,
      laneIntervalMs: lane.intervalMs,
      laneTargetCount: lane.targets.length,
      nextPollIntervalMs: lane.intervalMs,
    };
    console.log(
      `[ROUND] ${lane.name} start #${round} at ${new Date().toISOString()} | targets=${lane.targets.map((target) => target.name).join(', ')} | range=${MONITOR_START_DATE}..${MONITOR_END_DATE}`,
    );

    try {
      await writeMonitorHeartbeat({
        phase: 'round_start',
        roundId: round,
        laneId: lane.id,
        laneName: lane.name,
        laneOffsetMs: lane.offsetMs,
        laneIntervalMs: lane.intervalMs,
        laneTargetCount: lane.targets.length,
        nextPollIntervalMs: lane.intervalMs,
      });
      await runRound({ lane, roundId: round, snapshots });
    } catch (error) {
      console.log(
        `[ERROR] ${lane.name} round #${round} failed | ${error instanceof Error ? error.message : String(error)}`,
      );
    } finally {
      latestHeartbeatDetails = {
        phase: 'round_end',
        roundId: round,
        laneId: lane.id,
        laneName: lane.name,
        laneOffsetMs: lane.offsetMs,
        laneIntervalMs: lane.intervalMs,
        laneTargetCount: lane.targets.length,
        nextPollIntervalMs: lane.intervalMs,
      };
      await writeMonitorHeartbeat({
        phase: 'round_end',
        roundId: round,
        laneId: lane.id,
        laneName: lane.name,
        laneOffsetMs: lane.offsetMs,
        laneIntervalMs: lane.intervalMs,
        laneTargetCount: lane.targets.length,
        nextPollIntervalMs: lane.intervalMs,
      });
    }

    await sleep(lane.intervalMs);
  }
}

async function runRound({ lane, roundId, snapshots }) {
  const probeResults = await Promise.all(
    lane.targets.map(async (target) => ({ target, curr: await probeTarget(target) })),
  );

  const errorSummary = summarizeProbeErrors(probeResults);
  if (errorSummary.totalErrors === 0) {
    activeErrorIncident = null;
  } else if (errorSummary.totalErrors >= ERROR_BURST_TARGET_THRESHOLD) {
    activeErrorIncident = {
      signature: errorSummary.signature,
      startedAt: errorSummary.observedAt,
      updatedAt: errorSummary.observedAt,
      count: errorSummary.totalErrors,
      scope: 'global',
    };

    console.log(
      `[WARN] suppressing burst error incident | signature=${errorSummary.signature} | count=${errorSummary.totalErrors}/${probeResults.length}`,
    );
  } else if (activeErrorIncident) {
    activeErrorIncident.updatedAt = errorSummary.observedAt;
    activeErrorIncident.count = errorSummary.totalErrors;
  }

  for (const { target, curr } of probeResults) {
    await withTargetStateLock(target.name, async () => {
      if (stopSignals.size) {
        return;
      }

      const targetRecord = getTargetRecord(snapshots, target.name);
      const prev = getTargetSnapshot(targetRecord);
      const changedAt = new Date().toISOString();
      const currentError = getTargetError(targetRecord);
      const nextError = curr.status === 'ERROR' ? { streak: (currentError?.streak ?? 0) + 1 } : null;

      if (curr.status === 'ERROR' && activeErrorIncident) {
        setTargetError(targetRecord, {
          active: false,
          streak: nextError?.streak ?? 1,
          updatedAt: changedAt,
          roundId,
          prevStatus: prev?.status ?? null,
          lastSignature: normalizeErrorSignature(curr.errorMessage),
          suppressed: true,
        });
        console.log(
          `[WARN] ${target.name} burst error suppressed | signature=${normalizeErrorSignature(curr.errorMessage)} | scope=global`,
        );
        return;
      }

      const event = buildEvent(
        target,
        { ...prev, error: currentError },
        { ...curr, error: nextError },
        changedAt,
      );

      console.log(
        `[CHECK] ${lane.name} #${roundId} ${target.name} | ${curr.status}` +
          (curr.status === 'OPEN' ? ` | slots=${curr.slots.join(', ') || '-'}` : '') +
          (curr.status === 'ERROR' ? ' | error=true' : ''),
      );

      if (event) {
        console.log(`EVENT_JSON:${JSON.stringify(event)}`);
        await Promise.allSettled([pushToQclaw(event), pushToTelegram(event), writeAlertFile(event)]);
      }

      if (curr.status === 'ERROR') {
        const previousError = currentError ?? { active: false, streak: 0 };
        const nextStreak = (nextError?.streak ?? 0);
        const errorSignature = normalizeErrorSignature(curr.errorMessage);

        setTargetError(targetRecord, {
          active: previousError.active ?? false,
          streak: nextStreak,
          updatedAt: changedAt,
          roundId,
          prevStatus: prev?.status ?? null,
          lastSignature: errorSignature,
          lastNotifiedAt: previousError.lastNotifiedAt ?? null,
          cooldownUntil: previousError.cooldownUntil ?? null,
        });

        if (nextStreak < ERROR_CONFIRMATION_ROUNDS) {
          console.log(
            `[WARN] ${target.name} transient error deferred | streak=${nextStreak}/${ERROR_CONFIRMATION_ROUNDS}`,
          );
          return;
        }

        if (isWithinErrorCooldown(previousError, changedAt)) {
          console.log(
            `[WARN] ${target.name} error cooldown deferred | until=${previousError.cooldownUntil ?? '-'}`,
          );
          return;
        }

        if (!previousError.active) {
          setTargetError(targetRecord, {
            active: true,
            streak: nextStreak,
            updatedAt: changedAt,
            roundId,
            prevStatus: prev?.status ?? null,
            lastSignature: errorSignature,
            lastNotifiedAt: changedAt,
            cooldownUntil: addMillisecondsToIso(changedAt, ERROR_NOTIFICATION_COOLDOWN_MS),
          });
        }

        return;
      }

      if (currentError || prev?.status === 'ERROR') {
        setTargetError(targetRecord, {
          active: false,
          streak: 0,
          updatedAt: changedAt,
          roundId,
          prevStatus: prev?.status ?? null,
          lastSignature: currentError?.lastSignature ?? null,
          lastNotifiedAt: currentError?.lastNotifiedAt ?? null,
          cooldownUntil: currentError?.cooldownUntil ?? null,
          recoveredAt: changedAt,
        });
      } else {
        setTargetError(targetRecord, null);
      }

      setTargetSnapshot(targetRecord, {
        status: curr.status,
        slots: curr.slots,
        updatedAt: changedAt,
        roundId,
      });
    });
  }

  saveState(STATE_FILE, { targets: Object.fromEntries(snapshots.entries()) });
}

async function probeTarget(target) {
  if (!target.url) {
    return {
      status: 'ERROR',
      slots: [],
      errorMessage: 'missing target url',
    };
  }

  return withTargetProbeLock(target.name, async () => {
    const page = await browser.newPage();
    try {
      page.setDefaultTimeout(PAGE_TIMEOUT_MS);
      page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

      await page.goto(target.url, { waitUntil: 'domcontentloaded', timeout: PAGE_TIMEOUT_MS });
      await page.waitForTimeout(PAGE_GOTO_DELAY_MS);

      const rpcObservation = await probeTargetViaRpc(page);
      console.log(
        `[RPC] ${target.name} | ${rpcObservation.status} | slots=${rpcObservation.slots.length}`,
      );
      return rpcObservation;
    } catch (error) {
      console.log(
        `[ERROR] ${target.name} | ${error instanceof Error ? error.message : String(error)}`,
      );
      return {
        status: 'ERROR',
        slots: [],
        errorMessage: error instanceof Error ? error.message : String(error),
      };
    } finally {
      await page.close().catch(() => {});
    }
  });
}

async function probeTargetViaRpc(page) {
  const scheduleId = await resolveScheduleId(page);
    if (!scheduleId) {
      return {
        status: 'ERROR',
        slots: [],
        errorMessage: 'missing schedule id',
      };
    }

  try {
    const responseText = await fetchSlotsViaRpc(page, scheduleId, MONITOR_START_DATE, MONITOR_END_DATE);
    const slotEpochs = extractSlotEpochs(responseText);
    const slots = uniqueAndSortSlots(slotEpochs.map((epoch) => formatSlotEpoch(epoch, SLOT_TIMEZONE)));

    return {
      status: slots.length > 0 ? 'OPEN' : 'FULL',
      slots,
    };
  } catch (error) {
    console.log(`[WARN] rpc probe failed | ${error instanceof Error ? error.message : String(error)}`);
    await resetTargetPageFromPage(page).catch(() => {});
    return {
      status: 'ERROR',
      slots: [],
      errorMessage: error instanceof Error ? error.message : String(error),
    };
  }
}

async function fetchSlotsViaRpc(page, scheduleId, startDateIso, endDateIso) {
  const startEpoch = dateIsoToUtcEpoch(startDateIso);
  const endEpoch = dateIsoToUtcEpoch(nextDateIso(endDateIso));
  return page.evaluate(
    async ({ endpoint, scheduleIdValue, start, end }) => {
      const body = JSON.stringify([null, null, scheduleIdValue, null, [[start], [end]]]);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
          'x-user-agent': 'grpc-web-javascript/0.1',
          referer: 'https://calendar.google.com/',
        },
        body,
      });

      if (!response.ok) {
        throw new Error(`rpc response ${response.status}`);
      }

      return await response.text();
    },
    {
      endpoint:
        'https://calendar-pa.clients6.google.com/$rpc/google.internal.calendar.v1.AppointmentBookingService/ListAvailableSlots?%24httpHeaders=X-Goog-Api-Key%3AAIzaSyA7GKm43l8WNxlLTjsldq9z9n80CL6KW4U%0D%0AContent-Type%3Aapplication%2Fjson%2Bprotobuf%0D%0AX-User-Agent%3Agrpc-web-javascript%2F0.1%0D%0A',
      scheduleIdValue: scheduleId,
      start: startEpoch,
      end: endEpoch,
    },
  );
}

async function resolveScheduleId(page) {
  const candidates = [];

  const canonicalHref = await page
    .locator('link[rel="canonical"]')
    .first()
    .getAttribute('href')
    .catch(() => null);
  if (canonicalHref) {
    candidates.push(canonicalHref);
  }

  candidates.push(page.url());

  for (const candidate of candidates) {
    const match = /\/appointments\/schedules\/([^/?#]+)/.exec(candidate);
    if (match?.[1]) {
      return match[1];
    }
  }

  return null;
}

async function getTargetPage(targetName) {
  const existing = targetPages.get(targetName);
  if (existing && !existing.isClosed()) {
    return existing;
  }

  const page = await browser.newPage();
  targetPages.set(targetName, page);
  return page;
}

async function resetTargetPage(targetName) {
  const existing = targetPages.get(targetName);
  if (existing) {
    targetPages.delete(targetName);
    await existing.close().catch(() => {});
  }
}

async function resetTargetPageFromPage(targetPage) {
  for (const [name, existing] of targetPages.entries()) {
    if (existing === targetPage) {
      targetPages.delete(name);
      break;
    }
  }
  await targetPage.close().catch(() => {});
}

async function withTargetProbeLock(targetName, task) {
  const previous = targetProbeLocks.get(targetName) ?? Promise.resolve();
  let release = () => {};
  const current = new Promise((resolve) => {
    release = resolve;
  });
  const chain = previous.then(() => current);
  targetProbeLocks.set(targetName, chain);

  await previous;
  try {
    return await task();
  } finally {
    release();
    if (targetProbeLocks.get(targetName) === chain) {
      targetProbeLocks.delete(targetName);
    }
  }
}

async function withTargetStateLock(targetName, task) {
  const previous = targetStateLocks.get(targetName) ?? Promise.resolve();
  let release = () => {};
  const current = new Promise((resolve) => {
    release = resolve;
  });
  const chain = previous.then(() => current);
  targetStateLocks.set(targetName, chain);

  await previous;
  try {
    return await task();
  } finally {
    release();
    if (targetStateLocks.get(targetName) === chain) {
      targetStateLocks.delete(targetName);
    }
  }
}

function extractSlotEpochs(responseText) {
  const epochs = [];
  const matches = responseText.matchAll(/"(\d{10})"/g);
  for (const match of matches) {
    const epoch = Number.parseInt(match[1], 10);
    if (Number.isFinite(epoch)) {
      epochs.push(epoch);
    }
  }

  return [...new Set(epochs)].sort((a, b) => a - b);
}

function formatSlotEpoch(epochSeconds, timezone) {
  const date = new Date(epochSeconds * 1000);
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).formatToParts(date);

  const year = parts.find((part) => part.type === 'year')?.value ?? '1970';
  const month = parts.find((part) => part.type === 'month')?.value ?? '01';
  const day = parts.find((part) => part.type === 'day')?.value ?? '01';
  const hour = parts.find((part) => part.type === 'hour')?.value ?? '12';
  const minute = parts.find((part) => part.type === 'minute')?.value ?? '00';
  const dayPeriod = parts.find((part) => part.type === 'dayPeriod')?.value ?? 'AM';
  return `${year}-${month}-${day} ${hour}:${minute} ${dayPeriod}`;
}

function dateIsoToUtcEpoch(isoDate) {
  const parsed = parseDateString(isoDate);
  if (!parsed) {
    throw new Error(`invalid date: ${isoDate}`);
  }

  return Math.floor(parsed.getTime() / 1000);
}

function nextDateIso(isoDate) {
  const parsed = parseDateString(isoDate);
  if (!parsed) {
    throw new Error(`invalid date: ${isoDate}`);
  }

  parsed.setUTCDate(parsed.getUTCDate() + 1);
  return parsed.toISOString().slice(0, 10);
}

function parseDateString(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return null;
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  return new Date(Date.UTC(year, month - 1, day));
}

async function pushToQclaw(event) {
  if (!QCLAW_WEBHOOK_URL) {
    return;
  }

  try {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (QCLAW_WEBHOOK_SECRET) {
      headers['X-Webhook-Secret'] = QCLAW_WEBHOOK_SECRET;
    }

    const response = await fetch(QCLAW_WEBHOOK_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(event),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[WARN] qclaw push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(`[WARN] qclaw push error | ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function pushToTelegram(event) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    return;
  }

  try {
    const message = formatTelegramMessage(event);
    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
      body: new URLSearchParams({
        chat_id: TELEGRAM_CHAT_ID,
        text: message,
        disable_web_page_preview: 'true',
      }),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
      return;
    }

    console.log(`[INFO] telegram push ok | target=${event.target} | reason=${event.reason}`);
  } catch (error) {
    console.log(`[WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`);
  }
}

function formatTelegramMessage(event) {
  const slots = Array.isArray(event.currSlots) ? event.currSlots : [];
  const slotSummary =
    slots.length === 0
      ? '-'
      : slots.length <= 5
        ? slots.join(', ')
        : `${slots.slice(0, 5).join(', ')} … 共${slots.length}个时段`;

  const title =
    event.currStatus === 'ERROR'
      ? 'Mescladís 预约状态异常'
      : event.currStatus === 'OPEN'
        ? 'Mescladís 有可预约时段'
        : 'Mescladís 预约状态变化';

  return [
    title,
    `目标：${event.target}`,
    `状态：${event.currStatus}`,
    `原因：${event.reason}`,
    `时间：${event.changedAt}`,
    ...(event.prevStatus ? [`上次状态：${event.prevStatus}`] : []),
    ...(event.currStatus === 'OPEN' ? [`可预约时段：${slotSummary}`] : []),
    `链接：${event.url}`,
  ].join('\n');
}

async function writeAlertFile(event) {
  if (!ALERT_FILE_PATH || event.currStatus !== 'OPEN') {
    return;
  }

  const summary = [
    `target=${event.target}`,
    `status=${event.currStatus}`,
    `reason=${event.reason}`,
    `changedAt=${event.changedAt}`,
    `slots=${Array.isArray(event.currSlots) ? event.currSlots.join(', ') : ''}`,
    `url=${event.url}`,
    '',
    JSON.stringify(event),
  ].join('\n');

  try {
    await fs.promises.mkdir(path.dirname(ALERT_FILE_PATH), { recursive: true }).catch(() => {});
    const tempPath = `${ALERT_FILE_PATH}.${process.pid}.${Date.now()}.${randomUUID()}.tmp`;
    await fs.promises.writeFile(tempPath, `${summary}\n`, 'utf8');
    await fs.promises.rename(tempPath, ALERT_FILE_PATH);
  } catch (error) {
    console.log(
      `[WARN] unable to write alert file: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

async function seedAlertFile() {
  if (!ALERT_FILE_PATH) {
    return;
  }

  const now = new Date().toISOString();
  const seedEvent = {
    target: 'monitor',
    url: 'local-file-handoff',
    prevStatus: null,
    currStatus: 'UNKNOWN',
    prevSlots: [],
    currSlots: [],
    changedAt: now,
    reason: 'startup',
  };

  const summary = [
    `target=${seedEvent.target}`,
    `status=${seedEvent.currStatus}`,
    `reason=${seedEvent.reason}`,
    `changedAt=${seedEvent.changedAt}`,
    'slots=',
    `url=${seedEvent.url}`,
    '',
    JSON.stringify(seedEvent),
  ].join('\n');

  try {
    await fs.promises.mkdir(path.dirname(ALERT_FILE_PATH), { recursive: true }).catch(() => {});
    const tempPath = `${ALERT_FILE_PATH}.${process.pid}.${Date.now()}.${randomUUID()}.tmp`;
    await fs.promises.writeFile(tempPath, `${summary}\n`, 'utf8');
    await fs.promises.rename(tempPath, ALERT_FILE_PATH);
  } catch (error) {
    console.log(
      `[WARN] unable to seed alert file: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

async function writeMonitorHeartbeat(details) {
  if (!MONITOR_HEARTBEAT_FILE_PATH) {
    return;
  }

  const heartbeat = {
    process: 'monitor.js',
    pid: process.pid,
    startedAt: monitorStartedAt,
    writtenAt: new Date().toISOString(),
    phase: details.phase,
    roundId: details.roundId ?? null,
    laneId: details.laneId ?? null,
    laneName: details.laneName ?? null,
    laneOffsetMs: details.laneOffsetMs ?? null,
    laneIntervalMs: details.laneIntervalMs ?? null,
    laneTargetCount: details.laneTargetCount ?? null,
    nextPollIntervalMs: details.nextPollIntervalMs ?? null,
    pollIntervalMs: POLL_INTERVAL_MS,
    peakPollIntervalMs: PEAK_POLL_INTERVAL_MS,
    monitorTimezone: MONITOR_TIMEZONE,
    slotTimezone: SLOT_TIMEZONE,
    monitorStartDate: MONITOR_START_DATE,
    monitorEndDate: MONITOR_END_DATE,
    targetCount: targets.length,
  };

  try {
    await fs.promises.mkdir(path.dirname(MONITOR_HEARTBEAT_FILE_PATH), { recursive: true }).catch(() => {});
    const tempPath = `${MONITOR_HEARTBEAT_FILE_PATH}.${process.pid}.${Date.now()}.${randomUUID()}.tmp`;
    await fs.promises.writeFile(tempPath, `${JSON.stringify(heartbeat, null, 2)}\n`, 'utf8');
    await fs.promises.rename(tempPath, MONITOR_HEARTBEAT_FILE_PATH);
  } catch (error) {
    console.log(
      `[WARN] unable to write monitor heartbeat: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

function buildEvent(target, prev, curr, changedAt) {
  const prevStatus = prev?.status ?? null;
  const prevSlots = Array.isArray(prev?.slots) ? prev.slots : [];
  const currSlots = Array.isArray(curr.slots) ? curr.slots : [];

  if (curr.status === 'ERROR') {
    if (prev?.error?.active) {
      return null;
    }

    const errorStreak = curr.error?.streak ?? 0;
    if (errorStreak < ERROR_CONFIRMATION_ROUNDS) {
      return null;
    }

    if (isWithinErrorCooldown(prev?.error, changedAt)) {
      return null;
    }

    return {
      target: target.name,
      url: target.url,
      prevStatus,
      currStatus: curr.status,
      prevSlots,
      currSlots,
      changedAt,
      reason: 'error',
    };
  }

  if (!prev) {
    return null;
  }

  if (prev.status !== curr.status) {
    return {
      target: target.name,
      url: target.url,
      prevStatus,
      currStatus: curr.status,
      prevSlots,
      currSlots,
      changedAt,
      reason: 'status_changed',
    };
  }

  if (curr.status === 'OPEN' && !sameSlots(prevSlots, currSlots)) {
    return {
      target: target.name,
      url: target.url,
      prevStatus,
      currStatus: curr.status,
      prevSlots,
      currSlots,
      changedAt,
      reason: 'slots_changed',
    };
  }

  return null;
}

function sameSlots(prevSlots, currSlots) {
  if (prevSlots.length !== currSlots.length) {
    return false;
  }

  for (let index = 0; index < prevSlots.length; index += 1) {
    if (prevSlots[index] !== currSlots[index]) {
      return false;
    }
  }

  return true;
}

function normalizeErrorSignature(message) {
  const normalized = collapseWhitespace(String(message ?? ''));
  if (!normalized) {
    return 'error:unknown';
  }

  const lowered = normalized.toLowerCase();

  if (/net::err_internet_disconnected/i.test(normalized)) {
    return 'network:internet_disconnected';
  }
  if (/net::err_socket_not_connected/i.test(normalized)) {
    return 'network:socket_not_connected';
  }
  if (/net::err_connection_reset/i.test(normalized)) {
    return 'network:connection_reset';
  }
  if (/net::err_connection_closed/i.test(normalized)) {
    return 'network:connection_closed';
  }
  if (/failed to fetch/i.test(normalized)) {
    return 'network:fetch_failed';
  }
  if (
    /page\.goto:.*interrupted by another navigation/i.test(normalized) ||
    /interrupted by another navigation/i.test(normalized)
  ) {
    return 'navigation:interrupted';
  }
  if (/timeout .* exceeded/i.test(normalized) || /navigation timeout/i.test(lowered)) {
    return 'navigation:timeout';
  }
  if (/missing schedule id/i.test(lowered)) {
    return 'schedule:missing';
  }
  if (/rpc response \d+/i.test(normalized)) {
    return 'rpc:http_error';
  }

  return lowered
    .replace(/https?:\/\/\S+/g, '<url>')
    .replace(/calendar\.app\.google\/\S+/g, '<schedule>')
    .slice(0, 180);
}

function parseIsoTimestamp(value) {
  const parsed = Date.parse(String(value ?? ''));
  return Number.isFinite(parsed) ? parsed : null;
}

function addMillisecondsToIso(value, deltaMs) {
  const parsed = parseIsoTimestamp(value);
  if (parsed === null) {
    return null;
  }

  return new Date(parsed + deltaMs).toISOString();
}

function isWithinErrorCooldown(errorState, changedAt) {
  const cooldownUntilMs = parseIsoTimestamp(errorState?.cooldownUntil);
  if (cooldownUntilMs === null) {
    return false;
  }

  const changedAtMs = parseIsoTimestamp(changedAt);
  if (changedAtMs === null) {
    return false;
  }

  return changedAtMs < cooldownUntilMs;
}

function summarizeProbeErrors(probeResults) {
  const errorMessages = [];
  for (const result of probeResults) {
    if (result.curr.status === 'ERROR') {
      errorMessages.push(normalizeErrorSignature(result.curr.errorMessage));
    }
  }

  if (errorMessages.length === 0) {
    return {
      totalErrors: 0,
      shouldSuppress: false,
      signature: '',
      observedAt: new Date().toISOString(),
    };
  }

  const counts = new Map();
  for (const message of errorMessages) {
    counts.set(message, (counts.get(message) ?? 0) + 1);
  }

  let signature = errorMessages[0];
  let signatureCount = 0;
  for (const [message, count] of counts.entries()) {
    if (count > signatureCount) {
      signature = message;
      signatureCount = count;
    }
  }

  return {
    totalErrors: errorMessages.length,
    shouldSuppress: errorMessages.length >= ERROR_BURST_TARGET_THRESHOLD,
    signature,
    observedAt: new Date().toISOString(),
  };
}

function getTargetRecord(snapshots, targetName) {
  const existing = snapshots.get(targetName);
  if (existing && typeof existing === 'object') {
    if ('current' in existing) {
      if (!('error' in existing)) {
        existing.error = null;
      }
      return existing;
    }

    const migrated = {
      current: {
        status: existing.status ?? 'UNKNOWN',
        slots: Array.isArray(existing.slots) ? existing.slots : [],
        updatedAt: existing.updatedAt ?? null,
        roundId: Number.isFinite(existing.roundId) ? existing.roundId : 0,
      },
      error: null,
    };
    snapshots.set(targetName, migrated);
    return migrated;
  }

  const created = {
    current: null,
    error: null,
  };
  snapshots.set(targetName, created);
  return created;
}

function getTargetSnapshot(targetRecord) {
  return targetRecord.current ?? null;
}

function setTargetSnapshot(targetRecord, nextSnapshot) {
  targetRecord.current = nextSnapshot;
}

function getTargetError(targetRecord) {
  return targetRecord.error ?? null;
}

function setTargetError(targetRecord, nextError) {
  targetRecord.error = nextError;
}

function validateTargets(list) {
  if (list.length < 6) {
    throw new Error('targets must contain at least 6 entries');
  }

  const seenNames = new Set();
  for (const target of list) {
    if (!target.name || !target.url) {
      throw new Error(`missing name or url for target "${target.name ?? 'unknown'}"`);
    }
    if (seenNames.has(target.name)) {
      throw new Error(`duplicate target name "${target.name}"`);
    }
    seenNames.add(target.name);
  }
}

function buildMonitorLanes(list) {
  const laneOffsets = MONITOR_LANE_START_OFFSETS_MS.length ? MONITOR_LANE_START_OFFSETS_MS : [0];

  return laneOffsets
    .map((offsetMs, laneIndex) => ({
      id: laneIndex + 1,
      name: `lane-${laneIndex + 1}`,
      offsetMs,
      intervalMs: MONITOR_LANE_INTERVAL_MS,
      targets: list,
    }))
    .filter((lane) => lane.targets.length > 0);
}

function loadState() {
  try {
    if (!fs.existsSync(STATE_FILE)) {
      return { targets: {} };
    }

    const parsed = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    if (!parsed || typeof parsed !== 'object') {
      return { targets: {} };
    }

    return {
      targets: parsed.targets && typeof parsed.targets === 'object' ? parsed.targets : {},
    };
  } catch (error) {
    console.log(`[WARN] unable to read state file: ${error instanceof Error ? error.message : String(error)}`);
    return { targets: {} };
  }
}

function saveState(filePath, data) {
  const tempPath = `${filePath}.${process.pid}.${Date.now()}.${randomUUID()}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  fs.renameSync(tempPath, filePath);
}

function parseOffsetList(rawValue) {
  return rawValue
    .split(',')
    .map((part) => Number.parseInt(part.trim(), 10))
    .filter((value) => Number.isFinite(value) && value >= 0);
}

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) {
      continue;
    }

    const equalsIndex = trimmed.indexOf('=');
    if (equalsIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, equalsIndex).trim();
    let value = trimmed.slice(equalsIndex + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

function getPollIntervalForNow(timezone) {
  const currentHour = getHourInTimezone(timezone);
  if (currentHour >= PEAK_START_HOUR && currentHour < PEAK_END_HOUR) {
    return PEAK_POLL_INTERVAL_MS;
  }

  return POLL_INTERVAL_MS;
}

function getAlignedPollDelayForNow(timezone) {
  const intervalMs = getPollIntervalForNow(timezone);
  const wallClockMs = getWallClockMillisecondsInTimezone(timezone);
  const remainder = wallClockMs % intervalMs;
  return remainder === 0 ? intervalMs : intervalMs - remainder;
}

function describeAlignedTick(delayMs, timezone) {
  const intervalMs = getPollIntervalForNow(timezone);
  const wallClockMs = getWallClockMillisecondsInTimezone(timezone);
  const targetWallClockMs = wallClockMs + delayMs;
  const currentTick = formatWallClockTick(wallClockMs, timezone);
  const nextTick = formatWallClockTick(targetWallClockMs, timezone);
  return `${currentTick} -> ${nextTick} (${intervalMs}ms grid)`;
}

function formatWallClockTick(milliseconds, timezone) {
  const date = new Date(milliseconds);
  const parts = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: timezone,
  }).formatToParts(date);

  const hour = parts.find((part) => part.type === 'hour')?.value ?? '00';
  const minute = parts.find((part) => part.type === 'minute')?.value ?? '00';
  const second = parts.find((part) => part.type === 'second')?.value ?? '00';
  return `${hour}:${minute}:${second}`;
}

function getWallClockMillisecondsInTimezone(timezone) {
  const date = new Date();
  const parts = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: timezone,
  }).formatToParts(date);

  const hour = Number.parseInt(parts.find((part) => part.type === 'hour')?.value ?? '0', 10);
  const minute = Number.parseInt(parts.find((part) => part.type === 'minute')?.value ?? '0', 10);
  const second = Number.parseInt(parts.find((part) => part.type === 'second')?.value ?? '0', 10);
  return (((hour * 60) + minute) * 60 + second) * 1000 + date.getMilliseconds();
}

function getHourInTimezone(timezone) {
  const parts = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    hour12: false,
    timeZone: timezone,
  }).formatToParts(new Date());
  const hourPart = parts.find((part) => part.type === 'hour')?.value ?? '0';
  return Number.parseInt(hourPart, 10);
}

function readInteger(name, fallback) {
  const value = Number.parseInt(process.env[name] ?? '', 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function uniqueAndSortSlots(slots) {
  return [...new Set(slots.filter(Boolean))].sort((a, b) => slotSortKey(a) - slotSortKey(b) || a.localeCompare(b));
}

function slotSortKey(slot) {
  const match = slot.match(/^(\d{1,2}):(\d{2})(?:\s?(AM|PM))?$/i);
  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }

  let hours = Number(match[1]);
  const minutes = Number(match[2]);
  const meridiem = match[3]?.toUpperCase();

  if (meridiem === 'AM') {
    hours = hours === 12 ? 0 : hours;
  } else if (meridiem === 'PM') {
    hours = hours === 12 ? 12 : hours + 12;
  }

  return hours * 60 + minutes;
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

await main().catch((error) => {
  console.error(`[FATAL] ${error instanceof Error ? error.stack || error.message : String(error)}`);
  process.exitCode = 1;
});
