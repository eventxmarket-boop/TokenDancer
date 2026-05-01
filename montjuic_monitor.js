#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { parseLaneOffsets, runSerializedLaneScheduler } from './monitor_lane_scheduler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvFile(path.join(__dirname, '.env'));

const target = {
  name: process.env.MONTJUIC_TARGET_NAME ?? 'MONTJUIC',
  url: process.env.MONTJUIC_TARGET_URL ?? '',
};

const POLL_INTERVAL_MS = readInteger('MONTJUIC_POLL_INTERVAL_MS', 60_000);
const LANE_INTERVAL_MS = readInteger('MONITOR_LANE_INTERVAL_MS', POLL_INTERVAL_MS);
const LANE_START_OFFSETS_MS = parseLaneOffsets(process.env.MONITOR_LANE_START_OFFSETS_MS);
const PAGE_TIMEOUT_MS = readInteger('MONTJUIC_PAGE_TIMEOUT_MS', 45_000);
const PAGE_GOTO_DELAY_MS = readInteger('MONTJUIC_PAGE_GOTO_DELAY_MS', 900);
const CLICK_SETTLE_MS = readInteger('MONTJUIC_CLICK_SETTLE_MS', 1_200);
const MONITOR_TIMEZONE = process.env.MONTJUIC_TIMEZONE ?? 'Europe/Madrid';
const SLOT_TIMEZONE = process.env.MONTJUIC_SLOT_TIMEZONE ?? MONITOR_TIMEZONE;
const MONITOR_START_DATE = process.env.MONTJUIC_START_DATE ?? '2026-04-22';
const MONITOR_END_DATE = process.env.MONTJUIC_END_DATE ?? '2026-06-15';
const MONTJUIC_ALERT_FILE_PATH = (process.env.MONTJUIC_ALERT_FILE_PATH ?? '').trim();
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const STATE_FILE = resolveMonitorPath(process.env.MONTJUIC_STATE_FILE, 'montjuic_state.json');
const HEADLESS = (process.env.MONTJUIC_HEADLESS ?? 'true').toLowerCase() !== 'false';
const AUTO_SUBMIT = (process.env.MONTJUIC_AUTO_SUBMIT ?? 'false').toLowerCase() === 'true';
const CONFIRMATION_ALERT_ENABLED = (process.env.MONTJUIC_CONFIRMATION_ALERT_ENABLED ?? 'false').toLowerCase() === 'true';
const AUTOFILL_TRIGGER_MODE = (process.env.MONTJUIC_AUTOFILL_TRIGGER_MODE ?? 'transition').toLowerCase();
const SUPPRESS_STATUS_EVENTS = (process.env.MONTJUIC_SUPPRESS_STATUS_EVENTS ?? 'false').toLowerCase() === 'true';
const TELEGRAM_DISABLED = (process.env.MONTJUIC_TELEGRAM_DISABLED ?? 'false').toLowerCase() === 'true';
const EXECUTION_ONLY = (process.env.MONTJUIC_EXECUTION_ONLY ?? 'false').toLowerCase() === 'true';
const CONSUMER_MODE = (process.env.MONTJUIC_CONSUMER_MODE ?? 'false').toLowerCase() === 'true';
const BATCH_LIMIT = readInteger('MONTJUIC_BATCH_LIMIT', 0);
const PROFILES_CSV_PATH = (process.env.MONTJUIC_PROFILES_CSV_PATH ?? path.join(__dirname, 'montjuic_profiles_template.csv')).trim();
const SIGNAL_FILE_PATH = resolveMonitorPath(process.env.MONTJUIC_SIGNAL_FILE_PATH ?? process.env.MONTJUIC_ALERT_FILE_PATH, 'montjuic_alert.txt');
const SIGNAL_POLL_MS = readInteger('MONTJUIC_SIGNAL_POLL_MS', 250);
const monitorStartedAt = new Date().toISOString();
let profiles = loadProfiles();

const stopSignals = new Set();
let browser = null;
let browserContext = null;
let targetPage = null;
let executionPage = null;
let signalWatchQueued = false;
let signalWatchTimer = null;
let lastSignalHash = null;

process.on('SIGINT', () => stopSignals.add('SIGINT'));
process.on('SIGTERM', () => stopSignals.add('SIGTERM'));

async function main() {
  if (!target.url) {
    throw new Error('MONTJUIC_TARGET_URL is required');
  }

  const snapshots = new Map(Object.entries(loadState().targets ?? {}));
  if (CONSUMER_MODE) {
    await runExecutionConsumer({ snapshots });
    return;
  }

  await seedAlertFile();
  await writeMonitorHeartbeat({
    phase: 'startup',
    roundId: 0,
  });

  browser = await chromium.launch({ headless: HEADLESS });
  browserContext = await browser.newContext({
    timezoneId: SLOT_TIMEZONE,
    locale: 'en-US',
  });

  try {
    await runSerializedLaneScheduler({
      laneStartOffsetsMs: LANE_START_OFFSETS_MS,
      laneIntervalMs: LANE_INTERVAL_MS,
      stopSignals,
      onLaneStart: ({ laneIndex, offsetMs }) => {
        console.log(
          `[MONTJUIC] lane start | lane=${laneIndex} | offsetMs=${offsetMs} | target=${target.name}`,
        );
      },
      onTick: async ({ laneIndex, cycle }) => {
        const round = `${laneIndex}.${cycle}`;
        console.log(
          `[MONTJUIC] lane #${laneIndex} cycle #${cycle} start at ${new Date().toISOString()} | target=${target.name}`,
        );

        try {
          await writeMonitorHeartbeat({
            phase: 'round_start',
            roundId: round,
          });

          const curr = await probeTarget(target);
          const targetRecord = getTargetRecord(snapshots, target.name);
          const prev = getTargetSnapshot(targetRecord);
          const changedAt = new Date().toISOString();
          const event = buildEvent(target, prev, curr, changedAt);

          console.log(
            `[MONTJUIC] #${round} ${target.name} | ${curr.status}` +
              (curr.status === 'OPEN' ? ` | slots=${curr.slots.join(', ') || '-'}` : '') +
              (curr.status === 'ERROR' ? ` | error=${curr.reason ?? 'unknown'}` : ''),
          );

          if (event && !(SUPPRESS_STATUS_EVENTS && event.currStatus !== 'CONFIRMED')) {
            console.log(`EVENT_JSON:${JSON.stringify(event)}`);
            void pushToTelegram(event);
            await writeAlertFile(event);
          } else if (event) {
            console.log(
              `[MONTJUIC] status event suppressed | target=${target.name} | status=${event.currStatus} | reason=${event.reason}`,
            );
          }

          const shouldAutofill =
            curr.status === 'OPEN' &&
            profiles.length > 0 &&
            shouldTriggerAutofill({
              triggerMode: AUTOFILL_TRIGGER_MODE,
              prev,
              curr,
              targetRecord,
            });

          if (shouldAutofill) {
            setTargetAutofillState(targetRecord, {
              lastAutofillSignature: buildAutofillSignature(curr.status, curr.slots),
              lastAutofillAt: changedAt,
              lastAutofillMode: EXECUTION_ONLY ? 'signal_only' : AUTOFILL_TRIGGER_MODE,
            });

            if (EXECUTION_ONLY) {
              console.log(
                `[MONTJUIC][SIGNAL] ${target.name} | OPEN -> queued for executor | slots=${curr.slots.length}`,
              );
            } else {
              await runAutofillBatch({ slots: curr.slots, changedAt, targetRecord });
            }
          }

          const nextErrorCount =
            curr.status === 'ERROR'
              ? (Number.isFinite(prev?.errorCount) ? prev.errorCount : 0) + 1
              : 0;
          setTargetSnapshot(targetRecord, {
            status: curr.status,
            slots: curr.slots,
            updatedAt: changedAt,
            roundId: round,
            errorCount: nextErrorCount,
          });

          saveState(STATE_FILE, { targets: Object.fromEntries(snapshots.entries()) });
        } catch (error) {
          console.log(
            `[MONTJUIC][ERROR] round #${round} failed | ${
              error instanceof Error ? error.message : String(error)
            }`,
          );
        } finally {
          await writeMonitorHeartbeat({
            phase: 'round_end',
            roundId: round,
          });
        }
      },
    });
  } finally {
    await writeMonitorHeartbeat({
      phase: 'stopping',
      roundId: null,
    });

    if (targetPage) {
      await targetPage.close().catch(() => {});
      targetPage = null;
    }

    if (browserContext) {
      await browserContext.close().catch(() => {});
      browserContext = null;
    }

    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function probeTarget(currentTarget) {
  try {
    const page = await getTargetPage();
    page.setDefaultTimeout(PAGE_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

    await page.goto(currentTarget.url, { waitUntil: 'commit', timeout: Math.min(PAGE_TIMEOUT_MS, 20_000) });
    await page.waitForTimeout(PAGE_GOTO_DELAY_MS);

    const scheduleId = await resolveScheduleId(page);
    if (!scheduleId) {
      const pageText = collapseWhitespace(await page.locator('body').innerText({ timeout: 4_000 }).catch(() => ''));
      if (isFullText(pageText)) {
        return { status: 'FULL', slots: [], reason: 'no_availability_text' };
      }

      return { status: 'ERROR', slots: [], reason: 'schedule_id_not_found' };
    }

    const responseText = await fetchSlotsViaRpc(page, scheduleId, MONITOR_START_DATE, MONITOR_END_DATE);
    const slotEpochs = extractSlotEpochs(responseText);
    const slots = uniqueAndSortSlots(slotEpochs.map((epoch) => formatSlotEpoch(epoch, SLOT_TIMEZONE)));

    return {
      status: slots.length > 0 ? 'OPEN' : 'FULL',
      slots,
      reason: slots.length > 0 ? 'rpc_slots' : 'no_slots',
    };
  } catch (error) {
    return {
      status: 'ERROR',
      slots: [],
      reason: error instanceof Error ? error.message : String(error),
    };
  }
}

async function runAutofillBatch({ slots, changedAt, targetRecord }) {
  refreshProfiles();
  const batchProfiles = selectProfilesForAutofill(targetRecord, BATCH_LIMIT > 0 ? BATCH_LIMIT : profiles.length);
  const selectedSlots = slots.length > 0 ? slots : [];
  const gotoSettleMs = EXECUTION_ONLY ? Math.min(Math.max(PAGE_GOTO_DELAY_MS, 500), 700) : Math.max(PAGE_GOTO_DELAY_MS, 2_500);
  let anySlotClicked = false;
  console.log(
    `[MONTJUIC][AUTO] start | profiles=${batchProfiles.length} | slots=${selectedSlots.length} | changedAt=${changedAt}`,
  );

  const useSharedExecutionPage = CONSUMER_MODE || EXECUTION_ONLY;
  const sharedPage = useSharedExecutionPage ? await getExecutionPage() : null;

  for (const [index, profile] of batchProfiles.entries()) {
    if (stopSignals.size) {
      break;
    }

    const page = sharedPage ?? (await browser.newPage());
    try {
      page.setDefaultTimeout(PAGE_TIMEOUT_MS);
      page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

      if (!useSharedExecutionPage || index > 0 || !isLikelyBookingPageUrl(page.url(), target.url)) {
        try {
          await page.goto(target.url, { waitUntil: 'commit', timeout: Math.min(PAGE_TIMEOUT_MS, 20_000) });
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          console.log(`[MONTJUIC][AUTO][WARN] navigation soft-failed | ${message}`);
        }
      }
      await page.waitForTimeout(gotoSettleMs);

      const pageTimezone = SLOT_TIMEZONE;
      const bookingDateClicked = await clickBookingDate(page, selectedSlots, pageTimezone);
      if (bookingDateClicked) {
        await settleAfterAction(page, EXECUTION_ONLY ? Math.min(CLICK_SETTLE_MS, 500) : Math.max(CLICK_SETTLE_MS, 1_200));
      }

      if (bookingDateClicked) {
        await waitForSignalSlotVisible(page, selectedSlots, pageTimezone, EXECUTION_ONLY ? 8_000 : 6_000).catch(() => {});
      }

      const slotClicked = await clickExactSignalSlot(page, selectedSlots, pageTimezone);
      anySlotClicked = anySlotClicked || slotClicked;
      if (slotClicked) {
        await settleAfterAction(page, EXECUTION_ONLY ? Math.min(CLICK_SETTLE_MS, 700) : CLICK_SETTLE_MS);
      } else if (EXECUTION_ONLY) {
        const pageText = collapseWhitespace(await page.locator('body').innerText({ timeout: 2_000 }).catch(() => ''));
        const frameTexts = [];
        for (const frame of page.frames()) {
          const text = collapseWhitespace(await frame.locator('body').innerText({ timeout: 1_500 }).catch(() => ''));
          if (text) {
            frameTexts.push(text.slice(0, 300));
          }
        }
        console.log(
          `[MONTJUIC][AUTO][DEBUG] slot miss | frames=${page.frames().length} | pageText=${pageText.slice(0, 500).replace(/\s+/g, ' ')} | frameTexts=${frameTexts.join(' || ') || '-'}`,
        );
      }

      const formRoot = (await resolveContactFormRoot(page)) ?? page;
      await settleAfterAction(formRoot, EXECUTION_ONLY ? Math.min(Math.max(CLICK_SETTLE_MS, 900), 1_200) : Math.max(CLICK_SETTLE_MS, 2_500));
      const filledFields = await fillContactForm(formRoot, profile);

      console.log(
          `[MONTJUIC][AUTO] #${index + 1} ${profile.label || 'profile'} | slot=${
            slotClicked ? 'yes' : 'no'
        } | date=${bookingDateClicked ? 'yes' : 'no'} | fields=${filledFields.length ? filledFields.join(', ') : '-'} | submit=${
          AUTO_SUBMIT ? 'yes' : 'no'
        }`,
      );

      if (AUTO_SUBMIT) {
        const submitted = await clickContinueButton(formRoot);
        console.log(
          `[MONTJUIC][AUTO] #${index + 1} ${profile.label || 'profile'} | continue=${
            submitted ? 'yes' : 'no'
          }`,
        );
        if (submitted) {
          await settleAfterAction(formRoot, Math.min(CLICK_SETTLE_MS, 800));
          console.log(
            `[MONTJUIC][AUTO] #${index + 1} ${profile.label || 'profile'} | submitted=yes`,
          );
          if (CONFIRMATION_ALERT_ENABLED) {
            const confirmation = await detectConfirmationSnapshot(page);
            console.log(
              `[MONTJUIC][AUTO] #${index + 1} ${profile.label || 'profile'} | confirmation-skip=${
                confirmation.confirmed ? 'yes' : 'no'
              }${confirmation.summary ? ` | summary=${confirmation.summary}` : ''}`,
            );
          }
        }
      }

      advanceAutofillCursor(targetRecord, profile);
      if (useSharedExecutionPage && index < batchProfiles.length - 1) {
        await prepareExecutionPage(sharedPage ?? page, true);
      }
    } catch (error) {
      console.log(
        `[MONTJUIC][AUTO][ERROR] ${profile.label || `profile-${index + 1}`} | ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    } finally {
      if (!useSharedExecutionPage) {
        await page.close().catch(() => {});
      }
    }
  }

  return anySlotClicked;
}

async function runExecutionConsumer({ snapshots }) {
  await writeMonitorHeartbeat({
    phase: 'consumer_start',
    roundId: 0,
  });

  browser = await chromium.launch({ headless: HEADLESS });
  browserContext = await browser.newContext({
    timezoneId: SLOT_TIMEZONE,
    locale: 'en-US',
  });
  try {
    executionPage = await prepareExecutionPage();
    await seedSignalBaseline();
    fs.watchFile(SIGNAL_FILE_PATH, { interval: SIGNAL_POLL_MS }, () => {
      scheduleSignalWatch();
    });

    scheduleSignalWatch();

    while (!stopSignals.size) {
      await sleep(1000);
    }
  } finally {
    fs.unwatchFile(SIGNAL_FILE_PATH);

    if (executionPage) {
      await executionPage.close().catch(() => {});
      executionPage = null;
    }

    if (targetPage) {
      await targetPage.close().catch(() => {});
      targetPage = null;
    }

    if (browserContext) {
      await browserContext.close().catch(() => {});
      browserContext = null;
    }

    if (browser) {
      await browser.close().catch(() => {});
    }

    await writeMonitorHeartbeat({
      phase: 'consumer_stop',
      roundId: 0,
    });
  }
}

function scheduleSignalWatch() {
  signalWatchQueued = true;
  if (signalWatchTimer) {
    return;
  }

  signalWatchTimer = setTimeout(() => {
    signalWatchTimer = null;
    void drainSignalQueue();
  }, 250);
}

async function drainSignalQueue() {
  if (stopSignals.size) {
    return;
  }

  while (signalWatchQueued && !stopSignals.size) {
    signalWatchQueued = false;
    await processSignalFile();
  }
}

async function seedSignalBaseline() {
  if (!fs.existsSync(SIGNAL_FILE_PATH)) {
    console.log(`[MONTJUIC][CONSUMER] waiting for signal file | ${SIGNAL_FILE_PATH}`);
    return;
  }

  try {
    const content = await fs.promises.readFile(SIGNAL_FILE_PATH, 'utf8');
    console.log(`[MONTJUIC][CONSUMER] baseline observed | hash=${hashContent(content)}`);
  } catch (error) {
    console.log(
      `[MONTJUIC][CONSUMER] baseline read failed | ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

async function prepareExecutionPage(page = null, forceReload = false) {
  const nextPage = page ?? (await getExecutionPage());
  nextPage.setDefaultTimeout(PAGE_TIMEOUT_MS);
  nextPage.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);
  if (forceReload || !isLikelyBookingPageUrl(nextPage.url(), target.url)) {
    try {
      await nextPage.goto(target.url, { waitUntil: 'commit', timeout: Math.min(PAGE_TIMEOUT_MS, 20_000) });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.log(`[MONTJUIC][AUTO][WARN] navigation soft-failed | ${message}`);
    }
  }
  await nextPage.waitForTimeout(Math.min(Math.max(PAGE_GOTO_DELAY_MS, 700), 1_500));
  return nextPage;
}

async function getExecutionPage() {
  if (executionPage && !executionPage.isClosed()) {
    return executionPage;
  }

  executionPage = await (await getBrowserContext()).newPage();
  return executionPage;
}

async function getBrowserContext() {
  if (browserContext && !browserContext._closed) {
    return browserContext;
  }

  browserContext = await browser.newContext({
    timezoneId: SLOT_TIMEZONE,
    locale: 'en-US',
  });
  return browserContext;
}

async function processSignalFile() {
  try {
    const content = await fs.promises.readFile(SIGNAL_FILE_PATH, 'utf8');
    const hash = hashContent(content);

    if (hash === lastSignalHash) {
      return;
    }

    const parsed = parseSignalFile(content);
    if (!parsed) {
      console.log('[MONTJUIC][CONSUMER] parse failed, keeping previous baseline');
      return;
    }

    if (parsed.currStatus !== 'OPEN') {
      lastSignalHash = hash;
      return;
    }

    if (parsed.target && parsed.target !== target.name) {
      lastSignalHash = hash;
      return;
    }

    const snapshots = new Map(Object.entries(loadState().targets ?? {}));
    const targetRecord = getTargetRecord(snapshots, target.name);
    const signalSignature = buildAutofillSignature(parsed.currStatus, Array.isArray(parsed.currSlots) ? parsed.currSlots : []);
    const autofillState = getTargetAutofillState(targetRecord) ?? {};

    if (autofillState.lastConsumedSignalSignature === signalSignature) {
      lastSignalHash = hash;
      return;
    }

    console.log(
      `[MONTJUIC][CONSUMER] executing signal | target=${parsed.target || target.name} | slots=${Array.isArray(parsed.currSlots) ? parsed.currSlots.length : 0}`,
    );
    const autofillSucceeded = await runAutofillBatch({
      slots: Array.isArray(parsed.currSlots) ? parsed.currSlots : [],
      changedAt: parsed.changedAt ?? new Date().toISOString(),
      targetRecord,
    });

    if (autofillSucceeded) {
      setTargetAutofillState(targetRecord, {
        ...autofillState,
        lastAutofillSignature: signalSignature,
        lastConsumedSignalSignature: signalSignature,
        lastConsumedSignalAt: parsed.changedAt ?? new Date().toISOString(),
      });
    } else {
      setTargetAutofillState(targetRecord, {
        ...autofillState,
        lastAutofillSignature: null,
        lastConsumedSignalSignature: null,
        lastConsumedSignalAt: null,
      });
    }
    saveState(STATE_FILE, { targets: Object.fromEntries(snapshots.entries()) });
    lastSignalHash = hash;
  } catch (error) {
    console.log(
      `[MONTJUIC][CONSUMER][WARN] unable to process signal: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

function parseSignalFile(content) {
  const lines = content.split(/\r?\n/);
  const jsonLine = [...lines].reverse().find((line) => line.trim().startsWith('{'));
  if (!jsonLine) {
    return null;
  }

  try {
    const payload = JSON.parse(jsonLine);
    return {
      target: payload.target ?? null,
      url: payload.url ?? null,
      prevStatus: payload.prevStatus ?? null,
      currStatus: payload.currStatus ?? null,
      prevSlots: Array.isArray(payload.prevSlots) ? payload.prevSlots : [],
      currSlots: Array.isArray(payload.currSlots) ? payload.currSlots : [],
      changedAt: payload.changedAt ?? null,
      reason: payload.reason ?? null,
    };
  } catch {
    return null;
  }
}

function selectProfilesForAutofill(targetRecord, batchLimit) {
  if (!profiles.length) {
    return [];
  }

  const safeLimit = Math.max(Number.parseInt(String(batchLimit ?? 0), 10) || 0, 0);
  const limit = safeLimit > 0 ? safeLimit : profiles.length;
  const state = getTargetAutofillState(targetRecord) ?? {};
  const startIndex = Number.isInteger(state.nextProfileIndex) ? state.nextProfileIndex : 0;
  const selected = [];

  for (let offset = 0; offset < limit && offset < profiles.length; offset += 1) {
    const profile = profiles[(startIndex + offset) % profiles.length];
    if (profile) {
      selected.push(profile);
    }
  }

  return selected;
}

function refreshProfiles() {
  profiles = loadProfiles();
  return profiles;
}

function advanceAutofillCursor(targetRecord, profile) {
  if (!profile) {
    return;
  }

  const state = getTargetAutofillState(targetRecord) ?? {};
  const currentIndex = Number.isInteger(state.nextProfileIndex) ? state.nextProfileIndex : 0;
  const index = profiles.findIndex((entry) => entry && entry.label === profile.label);
  const nextProfileIndex = index >= 0 ? (index + 1) % Math.max(profiles.length, 1) : (currentIndex + 1) % Math.max(profiles.length, 1);

  setTargetAutofillState(targetRecord, {
    ...state,
    nextProfileIndex,
  });
}

async function clickExactSignalSlot(page, slots, timezone = SLOT_TIMEZONE) {
  if (await clickAnySignalSlotCandidate(page, slots, timezone, false)) {
    return true;
  }

  return clickAnySignalSlotCandidate(page, slots, timezone, true);
}

async function waitForSignalSlotVisible(page, slots, timezone = SLOT_TIMEZONE, timeoutMs = 6_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const candidate = await findVisibleSlotCandidate(page, slots, timezone, false);
    if (candidate) {
      return candidate;
    }
    await sleep(250);
  }
  return null;
}

async function findVisibleSlotCandidate(page, slots, timezone = SLOT_TIMEZONE, includeNearby = false) {
  const exactCandidates = buildSlotSearchCandidates(slots, timezone, includeNearby);

  for (const candidate of exactCandidates) {
    const regex = new RegExp(escapeRegExp(candidate), 'i');
    for (const scope of [page, ...page.frames()]) {
      const locators = [
        scope.getByRole('button', { name: regex }),
        scope.getByRole('link', { name: regex }),
        scope.getByText(regex),
        scope.locator('button', { hasText: regex }),
        scope.locator('a', { hasText: regex }),
        scope.locator('[role="button"]', { hasText: regex }),
        scope.locator('button, a, [role="button"]').filter({ hasText: regex }),
      ];

      for (const locator of locators) {
        try {
          const count = await locator.count().catch(() => 0);
          for (let index = 0; index < count; index += 1) {
            const candidateLocator = locator.nth(index);
            if (!(await candidateLocator.isVisible().catch(() => false))) {
              continue;
            }
            return candidate;
          }
        } catch {
          // keep searching
        }
      }
    }
  }

  return null;
}

async function clickAnySignalSlotCandidate(page, slots, timezone = SLOT_TIMEZONE, includeNearby = false) {
  const candidates = buildSlotSearchCandidates(slots, timezone, includeNearby);

  if (!candidates.length) {
    return false;
  }

  if (await clickSlotFromVisibleElements(page, candidates)) {
    return true;
  }

  for (const candidate of candidates) {
    const regex = new RegExp(escapeRegExp(candidate), 'i');
    for (const scope of [page, ...page.frames()]) {
      const locators = [
        scope.getByRole('button', { name: regex }),
        scope.getByRole('link', { name: regex }),
        scope.getByText(regex),
        scope.locator('button', { hasText: regex }),
        scope.locator('a', { hasText: regex }),
        scope.locator('[role="button"]', { hasText: regex }),
        scope.locator('button, a, [role="button"]').filter({ hasText: regex }),
      ];

      for (const locator of locators) {
        try {
          if (await clickFirstVisibleMatch(locator, { timeout: 1_500 })) {
            return true;
          }
        } catch {
          // continue exact search
        }
      }
    }
  }

  return false;
}

async function clickSlotFromVisibleElements(page, candidates) {
  const normalizedCandidates = candidates
    .map((candidate) => normalizeSlotMatchText(candidate))
    .filter(Boolean);

  if (!normalizedCandidates.length) {
    return false;
  }

  const scopes = [page, ...page.frames()];
  const selectors = [
    'button',
    'a',
    '[role="button"]',
    '[role="option"]',
    '[role="gridcell"]',
    '[tabindex]:not([tabindex="-1"])',
  ];

  for (const scope of scopes) {
    for (const selector of selectors) {
      const locator = scope.locator(selector);
      const count = await locator.count().catch(() => 0);
      for (let index = 0; index < count; index += 1) {
        const candidate = locator.nth(index);
        if (!(await candidate.isVisible().catch(() => false))) {
          continue;
        }
        if (!(await candidate.isEnabled().catch(() => true))) {
          continue;
        }

        const rawText = collapseWhitespace(
          await candidate.innerText({ timeout: 750 }).catch(() => ''),
        );
        const fallbackText = collapseWhitespace(
          await candidate.textContent({ timeout: 750 }).catch(() => ''),
        );
        const ariaLabel = collapseWhitespace(
          await candidate.getAttribute('aria-label').catch(() => ''),
        );
        const title = collapseWhitespace(await candidate.getAttribute('title').catch(() => ''));
        const haystacks = [rawText, fallbackText, ariaLabel, title]
          .filter(Boolean)
          .map((value) => normalizeSlotMatchText(value));

        if (!haystacks.length) {
          continue;
        }

        const matched = haystacks.some((haystack) =>
          normalizedCandidates.some((candidateText) => {
            if (!candidateText) {
              return false;
            }
            return (
              haystack === candidateText ||
              haystack.includes(candidateText) ||
              candidateText.includes(haystack)
            );
          }),
        );

        if (!matched) {
          continue;
        }

        await candidate.scrollIntoViewIfNeeded({ timeout: 750 }).catch(() => {});
        try {
          await candidate.click({ timeout: 1_500, noWaitAfter: true });
          return true;
        } catch {
          try {
            await candidate.evaluate((element) => {
              element.dispatchEvent(
                new MouseEvent('click', { bubbles: true, cancelable: true, view: window }),
              );
            });
            return true;
          } catch {
            // keep searching other visible elements
          }
        }
      }
    }
  }

  return false;
}

function normalizeSlotMatchText(text) {
  return collapseWhitespace(String(text))
    .toLowerCase()
    .replace(/[^\w:/-]+/g, '');
}

function buildSlotSearchCandidates(slots, timezone = SLOT_TIMEZONE, includeNearby = false) {
  const exactCandidates = [];
  const seen = new Set();
  for (const slot of slots.slice(0, 5)) {
    for (const candidate of buildSlotCandidates(slot, timezone)) {
      const normalized = collapseWhitespace(candidate).toLowerCase();
      if (!normalized || seen.has(normalized)) {
        continue;
      }
      seen.add(normalized);
      exactCandidates.push(candidate);
    }

    if (includeNearby) {
      for (const candidate of buildNearbySlotCandidates(slot, timezone)) {
        const normalized = collapseWhitespace(candidate).toLowerCase();
        if (!normalized || seen.has(normalized)) {
          continue;
        }
        seen.add(normalized);
        exactCandidates.push(candidate);
      }
    }
  }

  return exactCandidates;
}

function buildNearbySlotCandidates(slot, timezone = SLOT_TIMEZONE) {
  const normalized = collapseWhitespace(String(slot));
  const resolved = convertSlotStringTimezone(normalized, SLOT_TIMEZONE, timezone) ?? normalized;
  const match = /^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)$/i.exec(resolved);
  if (!match) {
    return [];
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  const hour = Number.parseInt(match[4], 10);
  const minute = match[5];
  const meridiem = match[6].toUpperCase();
  const base = new Date(Date.UTC(year, month - 1, day, convertTo24Hour(hour, meridiem), Number.parseInt(minute, 10)));
  const offsets = [-1, 1];
  const variants = [];

  for (const offset of offsets) {
    const adjusted = new Date(base.getTime() + offset * 60 * 60 * 1000);
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).formatToParts(adjusted);
    const outYear = parts.find((part) => part.type === 'year')?.value ?? '1970';
    const outMonth = parts.find((part) => part.type === 'month')?.value ?? '01';
    const outDay = parts.find((part) => part.type === 'day')?.value ?? '01';
    const outHour = parts.find((part) => part.type === 'hour')?.value ?? '12';
    const outMinute = parts.find((part) => part.type === 'minute')?.value ?? '00';
    const outMeridiem = parts.find((part) => part.type === 'dayPeriod')?.value ?? 'AM';
    const hh12 = String(Number.parseInt(outHour, 10));
    const hh12Padded = hh12.padStart(2, '0');
    const time12 = `${hh12}:${outMinute} ${outMeridiem.toUpperCase()}`;
    const time12Padded = `${hh12Padded}:${outMinute} ${outMeridiem.toUpperCase()}`;
    const time12Compact = `${hh12}:${outMinute}${outMeridiem.toLowerCase()}`;
    const time12PaddedCompact = `${hh12Padded}:${outMinute}${outMeridiem.toLowerCase()}`;
    const time12TitleCompact = `${hh12}:${outMinute}${outMeridiem.toUpperCase()}`;
    const time12PaddedTitleCompact = `${hh12Padded}:${outMinute}${outMeridiem.toUpperCase()}`;
    const time24 = `${String(convertTo24Hour(Number.parseInt(outHour, 10), outMeridiem.toUpperCase())).padStart(2, '0')}:${outMinute}`;
    variants.push(
      `${outYear}-${outMonth}-${outDay} ${time12}`,
      `${outYear}-${outMonth}-${outDay} ${time12Padded}`,
      `${outYear}-${outMonth}-${outDay} ${time12Compact}`,
      `${outYear}-${outMonth}-${outDay} ${time12PaddedCompact}`,
      `${outYear}-${outMonth}-${outDay} ${time12TitleCompact}`,
      `${outYear}-${outMonth}-${outDay} ${time12PaddedTitleCompact}`,
      `${outYear}-${outMonth}-${outDay} ${time24}`,
      time12,
      time12Padded,
      time12Compact,
      time12PaddedCompact,
      time12TitleCompact,
      time12PaddedTitleCompact,
      time24,
    );
  }

  return variants;
}

async function clickBookingDate(page, slots, timezone = SLOT_TIMEZONE) {
  const targetMeta = extractSlotDateMeta(slots[0], timezone);
  if (targetMeta) {
    await alignCalendarMonth(page, targetMeta).catch(() => {});
  }

  const candidates = [];
  const seen = new Set();

  for (const slot of slots.slice(0, 5)) {
    for (const candidate of buildDateCandidates(slot, timezone)) {
      const normalized = collapseWhitespace(candidate).toLowerCase();
      if (!normalized || seen.has(normalized)) {
        continue;
      }
      seen.add(normalized);
      candidates.push(candidate);
    }
  }

  for (let attempt = 0; attempt < 4; attempt += 1) {
    for (const candidate of candidates) {
      const regex = new RegExp(escapeRegExp(candidate), 'i');
      const scopes = [page, ...page.frames()];

      for (const scope of scopes) {
        const locators = [
          scope.getByRole('button', { name: regex }),
          scope.getByRole('link', { name: regex }),
          scope.getByText(regex),
          scope.locator('button', { hasText: regex }),
          scope.locator('a', { hasText: regex }),
          scope.locator('[role="button"]', { hasText: regex }),
          scope.locator('button, a, [role="button"]').filter({ hasText: regex }),
        ];

        for (const locator of locators) {
          try {
            if (await clickFirstVisibleMatch(locator, { timeout: 2_000 })) {
              return true;
            }
          } catch {
            // try next candidate
          }
        }
      }
    }

    await sleep(250);
  }

  return false;
}

async function alignCalendarMonth(page, targetMeta) {
  if (!targetMeta) {
    return false;
  }

  const targetMonthIndex = targetMeta.monthIndex;
  const targetYear = targetMeta.year;
  const targetLabelVariants = [
    `${targetMeta.monthLong} ${targetYear}`,
    `${targetMeta.monthShort} ${targetYear}`,
  ].map((value) => collapseWhitespace(value).toLowerCase());

  for (let attempt = 0; attempt < 12; attempt += 1) {
    const visibleText = collapseWhitespace(await page.locator('body').innerText({ timeout: 2_500 }).catch(() => ''));
    const lowered = visibleText.toLowerCase();
    if (targetLabelVariants.some((label) => lowered.includes(label))) {
      return true;
    }

    const current = extractVisibleMonthYear(visibleText);
    if (current && Number.isFinite(current.year) && Number.isFinite(current.monthIndex)) {
      if (current.year > targetYear || (current.year === targetYear && current.monthIndex > targetMonthIndex)) {
        if (!(await clickMonthNav(page, 'previous'))) {
          break;
        }
        await page.waitForTimeout(500).catch(() => {});
        continue;
      }
      if (current.year < targetYear || (current.year === targetYear && current.monthIndex < targetMonthIndex)) {
        if (!(await clickMonthNav(page, 'next'))) {
          break;
        }
        await page.waitForTimeout(500).catch(() => {});
        continue;
      }
      return true;
    }

    if (targetYear > new Date().getUTCFullYear() || targetMonthIndex > 0) {
      if (!(await clickMonthNav(page, 'next'))) {
        break;
      }
      await page.waitForTimeout(500).catch(() => {});
      continue;
    }
    break;
  }

  return false;
}

async function clickMonthNav(page, direction) {
  const regex = direction === 'next' ? /next month|chevron_right/i : /previous month|chevron_left/i;
  const scopes = [page, ...page.frames()];
  for (const scope of scopes) {
    const locators = [
      scope.getByRole('button', { name: regex }),
      scope.getByRole('link', { name: regex }),
      scope.getByLabel(regex),
      scope.getByText(regex),
      scope.locator('button', { hasText: regex }),
      scope.locator('a', { hasText: regex }),
      scope.locator('[role="button"]', { hasText: regex }),
      scope.locator('button, a, [role="button"]').filter({ hasText: regex }),
    ];
    for (const locator of locators) {
      try {
        if (await clickFirstVisibleMatch(locator, { timeout: 2_000 })) {
          return true;
        }
      } catch {
        // continue searching
      }
    }
  }
  return false;
}

function extractVisibleMonthYear(text) {
  const months = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december',
  ];
  const lowered = collapseWhitespace(text).toLowerCase();
  for (let index = 0; index < months.length; index += 1) {
    const month = months[index];
    const regex = new RegExp(`\b${month}\s+(\d{4})\b`, 'i');
    const match = regex.exec(lowered);
    if (match) {
      return { monthIndex: index, year: Number.parseInt(match[1], 10) };
    }
  }
  return null;
}

async function clickFirstVisibleMatch(locator, { timeout = 2_000 } = {}) {
  const count = await locator.count().catch(() => 0);
  for (let index = 0; index < count; index += 1) {
    const candidate = locator.nth(index);
    const visible = await candidate.isVisible().catch(() => false);
    if (!visible) {
      continue;
    }

    const enabled = await candidate.isEnabled().catch(() => true);
    if (!enabled) {
      continue;
    }

    await candidate.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
    try {
      await candidate.click({ timeout, noWaitAfter: true });
      return true;
    } catch {
      try {
        await candidate.click({ timeout, noWaitAfter: true, force: true });
        return true;
      } catch {
        // try next visible match
      }
    }
  }

  return false;
}

function isLikelyBookingPageUrl(currentUrl, targetUrl) {
  const url = String(currentUrl ?? '').trim();
  const target = String(targetUrl ?? '').trim();
  if (!url) {
    return false;
  }
  if (url === target) {
    return true;
  }
  if (/calendar\.(app|google)\.com/i.test(url) && /appointments\/schedules\//i.test(url)) {
    return true;
  }
  if (/bookings\.cloud\.microsoft/i.test(url)) {
    return true;
  }
  return false;
}

async function detectDisplayedTimezone(page) {
  const fragments = [];
  const pageText = collapseWhitespace(await page.locator('body').innerText({ timeout: 3_000 }).catch(() => ''));
  if (pageText) {
    fragments.push(pageText);
  }

  for (const frame of page.frames()) {
    try {
      const text = collapseWhitespace(await frame.locator('body').innerText({ timeout: 1_500 }).catch(() => ''));
      if (text) {
        fragments.push(text);
      }
    } catch {
      // ignore
    }
  }

  const combined = fragments.join(' ').replace(/\s+/g, ' ').trim();
  const gmtMatch = /\bGMT([+-]\d{2}:\d{2})\b/i.exec(combined);
  if (gmtMatch) {
    return gmtOffsetToTimezone(gmtMatch[1]);
  }

  if (/Singapore Standard Time/i.test(combined)) {
    return 'Asia/Singapore';
  }

  if (/Central European Time|Madrid|Spain/i.test(combined)) {
    return 'Europe/Madrid';
  }

  return null;
}

async function fillContactForm(root, profile) {
  const filled = [];
  const fieldDefs = [
    {
      key: 'surname',
      value: profile.surname,
      patterns: [/apellido/i, /surname/i, /last name/i, /姓氏/i],
    },
    {
      key: 'givenName',
      value: profile.givenName,
      patterns: [/^nombre$/i, /given name/i, /first name/i, /名字/i],
    },
    {
      key: 'email',
      value: profile.email,
      patterns: [/correo/i, /email/i, /e-mail/i, /email address/i, /邮箱/i],
    },
    {
      key: 'phone',
      value: profile.phone,
      patterns: [/tel[eé]fono/i, /phone/i, /phone number/i, /电话号码/i],
    },
    {
      key: 'fullAddress',
      value: profile.fullAddress,
      patterns: [
        /direcci[oó]n completa/i,
        /direcci[oó]n completa \(calle, numero, ciudad, c[oó]digo postal, provincia\)/i,
        /calle, numero, ciudad, c[oó]digo postal, provincia/i,
        /full address/i,
      ],
    },
    {
      key: 'documentNumber',
      value: profile.documentNumber,
      patterns: [/n[uú]mero de documento/i, /numero de documento/i, /document number/i],
    },
    {
      key: 'nationality',
      value: profile.nationality,
      patterns: [/nacionalidad/i, /nationality/i],
    },
    {
      key: 'birthDate',
      value: profile.birthDate,
      patterns: [/fecha de nacimiento/i, /birth date/i, /date of birth/i, /\bdob\b/i],
    },
  ];

  for (const def of fieldDefs) {
    if (!def.value) {
      continue;
    }
    const locator = await findInputLocator(root, def.patterns);
    if (!locator) {
      continue;
    }

    try {
      await locator.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
      const tagName = await locator.evaluate((element) => element.tagName.toLowerCase()).catch(() => 'input');
      if (tagName === 'select') {
        await selectOptionByValueOrLabel(locator, def.value);
      } else if (tagName === 'textarea' || tagName === 'input') {
        const normalizedValue = String(def.value);
        await locator.fill(normalizedValue, { timeout: 2_000 });
      } else {
        await locator.click({ timeout: 1_000 });
        await locator.pressSequentially(String(def.value), { delay: 15 });
      }
      const verified = await verifyFilledValue(locator, def.value, def.key).catch(() => false);
      filled.push(verified ? def.key : `${def.key}!`);
    } catch (error) {
      console.log(
        `[MONTJUIC][AUTO][WARN] ${def.key} fill failed | ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }

  const verifiedCount = filled.filter((entry) => !String(entry).endsWith('!')).length;
  if (verifiedCount < 8) {
    const orderFallback = [
      ['givenName', profile.givenName],
      ['surname', profile.surname],
      ['email', profile.email],
      ['phone', profile.phone],
      ['documentNumber', profile.documentNumber],
      ['fullAddress', profile.fullAddress],
      ['nationality', profile.nationality],
      ['birthDate', profile.birthDate],
    ];
    const orderedControls = root.locator(
      'input:not([name=\"g-recaptcha-response\"]), textarea:not([name=\"g-recaptcha-response\"]), select, [contenteditable=\"true\"]',
    );
    const controlCount = await orderedControls.count().catch(() => 0);
    if (controlCount >= 4) {
      let orderIndex = 0;
      for (const [key, value] of orderFallback) {
        if (!value) {
          orderIndex += 1;
          continue;
        }

        try {
          const locator = orderedControls.nth(orderIndex);
          const tagName = await locator.evaluate((element) => element.tagName.toLowerCase()).catch(() => 'input');
          if (tagName === 'select') {
            await selectOptionByValueOrLabel(locator, value);
          } else if (tagName === 'textarea' || tagName === 'input') {
            await locator.fill(String(value), { timeout: 2_000 });
          } else {
            await locator.click({ timeout: 1_000 });
            await locator.pressSequentially(String(value), { delay: 15 });
          }
          const verified = await verifyFilledValue(locator, value, key).catch(() => false);
          filled.push(verified ? `${key}:order` : `${key}:order!`);
        } catch (error) {
          console.log(
            `[MONTJUIC][AUTO][WARN] ${key} order fill failed | ${
              error instanceof Error ? error.message : String(error)
            }`,
          );
        }

        orderIndex += 1;
      }
    }
  }

  if (!filled.some((entry) => String(entry).replace(/!$/, '').startsWith('birthDate'))) {
    const birthDateLocator = await findBirthDateLocator(root, profile.birthDate);
    if (birthDateLocator) {
      try {
        await birthDateLocator.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
        const tagName = await birthDateLocator.evaluate((element) => element.tagName.toLowerCase()).catch(() => 'input');
        if (tagName === 'select') {
          await selectOptionByValueOrLabel(birthDateLocator, profile.birthDate);
        } else if (tagName === 'textarea' || tagName === 'input') {
          await birthDateLocator.fill(String(profile.birthDate), { timeout: 2_000 });
        } else {
          await birthDateLocator.click({ timeout: 1_000 });
          await birthDateLocator.pressSequentially(String(profile.birthDate), { delay: 15 });
        }
        const verified = await verifyFilledValue(birthDateLocator, profile.birthDate, 'birthDate').catch(() => false);
        filled.push(verified ? 'birthDate:rescue' : 'birthDate:rescue!');
      } catch (error) {
        console.log(
          `[MONTJUIC][AUTO][WARN] birthDate rescue failed | ${error instanceof Error ? error.message : String(error)}`,
        );
      }
    }
  }

  return filled;
}

async function findBirthDateLocator(root, value) {
  const patterns = [
    /fecha de nacimiento/i,
    /birth date/i,
    /date of birth/i,
    /\bdob\b/i,
    /birthday/i,
    /nacimiento/i,
    /dd\/mm\/yyyy/i,
    /mm\/dd\/yyyy/i,
    /yyyy/i,
    /fecha/i,
  ];

  const direct = await findInputLocator(root, patterns);
  if (direct) {
    return direct;
  }

  const locator = root.locator(
    'input[type="date"], input[placeholder*="fecha" i], input[placeholder*="birth" i], input[placeholder*="dob" i], input[placeholder*="dd" i], input[placeholder*="mm" i], input[aria-label*="fecha" i], input[aria-label*="birth" i], input[aria-label*="dob" i]',
  );
  const count = await locator.count().catch(() => 0);
  for (let index = 0; index < count; index += 1) {
    const candidate = locator.nth(index);
    if (await candidate.isVisible().catch(() => false)) {
      return candidate;
    }
  }

  const fallback = root
    .locator('input:not([name="g-recaptcha-response"]), textarea:not([name="g-recaptcha-response"]), select')
    .filter({ hasNotText: /captcha/i });
  const fallbackCount = await fallback.count().catch(() => 0);
  for (let index = fallbackCount - 1; index >= 0; index -= 1) {
    const candidate = fallback.nth(index);
    if (await candidate.isVisible().catch(() => false)) {
      return candidate;
    }
  }

  return null;
}

async function clickContinueButton(root) {
  const regexes = [
    /^Siguiente$/i,
    /Continuar/i,
    /\bNext\b/i,
    /Confirmar/i,
    /Reservar/i,
    /^预定$/i,
    /^預定$/i,
    /^预订$/i,
    /^預訂$/i,
    /取消\s*\/\s*预定/i,
    /取消\s*\/\s*預定/i,
    /取消\s*\/\s*预订/i,
    /取消\s*\/\s*預訂/i,
    /^Book$/i,
    /^Book now$/i,
    /^Submit$/i,
    /submit request/i,
    /request is being submitted/i,
  ];
  for (const regex of regexes) {
    const locators = [
      root.getByRole?.('button', { name: regex }),
      root.getByRole?.('link', { name: regex }),
      root.getByText?.(regex),
      root.locator?.('button', { hasText: regex }),
      root.locator?.('a', { hasText: regex }),
      root.locator?.('[role="button"]', { hasText: regex }),
    ];

    for (const locator of locators) {
      if (!locator) {
        continue;
      }

      try {
        const resolved = locator.first();
        if ((await resolved.count().catch(() => 0)) === 0) {
          continue;
        }
        await resolved.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
        try {
          await resolved.click({ timeout: 2_000, noWaitAfter: true });
          return true;
        } catch {
          await resolved.click({ timeout: 2_000, noWaitAfter: true, force: true });
          return true;
        }
      } catch {
        // keep trying
      }
    }
  }

  return false;
}

async function settleAfterAction(root, waitMs) {
  await root.waitForTimeout(Math.max(Number(waitMs) || 0, 0)).catch(() => {});
}

async function detectConfirmationSnapshot(page) {
  const fragments = [];
  const pageText = collapseWhitespace(await page.locator('body').innerText({ timeout: 3_000 }).catch(() => ''));
  if (pageText) {
    fragments.push(pageText);
  }

  for (const frame of page.frames()) {
    try {
      const text = collapseWhitespace(await frame.locator('body').innerText({ timeout: 2_000 }).catch(() => ''));
      if (text) {
        fragments.push(text);
      }
    } catch {
      // keep looking
    }
  }

  const combined = collapseWhitespace(fragments.join(' \n '));
  const lowered = combined.toLowerCase();
  const confirmed = [
    'confirmación',
    'confirmacion',
    'confirmed',
    'confirmation',
    'booking confirmed',
    'appointment confirmed',
    'tu cita',
    'cita confirmada',
    'reserva confirmada',
    'reserva creada',
    'reservación creada',
    '已确认预订',
    '邮件已发送至',
    '请取消预约',
    '需要变更吗',
    'gracias',
    'success',
  ].some((phrase) => lowered.includes(phrase));

  return {
    confirmed,
    summary: combined.slice(0, 600),
  };
}

async function resolveContactFormRoot(page) {
  const candidates = [];
  for (const frame of page.frames()) {
    try {
      const text = collapseWhitespace(await frame.locator('body').innerText({ timeout: 2_500 }).catch(() => ''));
      const hasFormLabel = [
        'apellido',
        'nombre',
        'correo',
        'email',
        'teléfono',
        'telefono',
        'número de documento',
        'numero de documento',
        'dirección completa',
        'dirección completa (calle, numero, ciudad, código postal, provincia)',
        'calle, numero, ciudad, código postal, provincia',
        'nacionalidad',
        'nationality',
        'fecha de nacimiento',
        'birth date',
        'siguiente',
        'continuar',
      ].some((phrase) => text.toLowerCase().includes(phrase));
      const inputCount = await frame.locator('input, textarea, select').count().catch(() => 0);
      if (hasFormLabel || inputCount > 0) {
        let score = 0;
        if (hasFormLabel) score += 4;
        score += Math.min(inputCount, 6);
        score += Math.min(getFrameDepth(frame), 4);
        candidates.push({ frame, score });
      }
    } catch {
      // keep looking
    }
  }

  if (candidates.length > 0) {
    candidates.sort((left, right) => right.score - left.score);
    return candidates[0].frame;
  }

  return page;
}

async function findInputLocator(root, patterns) {
  const selector = 'input, textarea, select, [contenteditable="true"]';
  const locator = root.locator(selector);
  const count = await locator.count().catch(() => 0);
  if (!count) {
    return null;
  }

  const rows = await locator.evaluateAll((elements) =>
    elements.map((element, index) => {
      const associatedLabel = element.labels
        ? Array.from(element.labels)
            .map((label) => label.textContent || '')
            .join(' ')
        : '';
      const closestLabel = element.closest('label')?.textContent || '';
      const attrs = [
        element.getAttribute('aria-label'),
        element.getAttribute('placeholder'),
        element.getAttribute('name'),
        element.getAttribute('autocomplete'),
        element.getAttribute('id'),
        element.getAttribute('type'),
        associatedLabel,
        closestLabel,
        element.textContent,
      ]
        .filter(Boolean)
        .map((value) => String(value).replace(/\s+/g, ' ').trim())
        .filter(Boolean);
      return { index, haystack: attrs.join(' | ') };
    }),
  );

  for (const row of rows) {
    if (patterns.some((pattern) => pattern.test(row.haystack))) {
      const candidate = locator.nth(row.index);
      if (await candidate.isVisible().catch(() => false)) {
        return candidate;
      }
    }
  }

  return null;
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

function buildSlotCandidates(slot, timezone = SLOT_TIMEZONE) {
  const normalized = collapseWhitespace(String(slot));
  const resolved = convertSlotStringTimezone(normalized, SLOT_TIMEZONE, timezone) ?? normalized;
  const match = /^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)$/i.exec(resolved);
  if (!match) {
    return [resolved];
  }

  const year = match[1];
  const month = match[2];
  const day = match[3];
  const hour = Number.parseInt(match[4], 10);
  const minute = match[5];
  const meridiem = match[6].toUpperCase();
  const hh12 = String(hour).padStart(2, '0');
  const hh12NoPad = String(hour);
  const hour24 = convertTo24Hour(hour, meridiem);
  const dateIso = `${year}-${month}-${day}`;
  const dateSlashed = `${month}/${day}`;
  const dateDotted = `${day}/${month}`;
  const time12 = `${hh12NoPad}:${minute} ${meridiem}`;
  const time12Padded = `${hh12}:${minute} ${meridiem}`;
  const time24 = `${String(hour24).padStart(2, '0')}:${minute}`;
  const time12Compact = `${hh12NoPad}:${minute}${meridiem.toLowerCase()}`;
  const time12PaddedCompact = `${hh12}:${minute}${meridiem.toLowerCase()}`;
  const time12TitleCompact = `${hh12NoPad}:${minute}${meridiem}`;
  const time12PaddedTitleCompact = `${hh12}:${minute}${meridiem}`;
  const dateParts = new Date(Date.UTC(Number.parseInt(year, 10), Number.parseInt(month, 10) - 1, Number.parseInt(day, 10)));
  const monthLong = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    month: 'long',
  }).format(dateParts);
  const monthShort = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    month: 'short',
  }).format(dateParts);
  const monthDay = `${monthLong} ${Number.parseInt(day, 10)}`;
  const monthDayShort = `${monthShort} ${Number.parseInt(day, 10)}`;
  const weekdayLong = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    weekday: 'long',
  }).format(dateParts);
  const weekdayShort = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    weekday: 'short',
  }).format(dateParts);
  const fullDateLabel = `${weekdayLong}, ${monthLong} ${Number.parseInt(day, 10)}, ${year}`;
  const fullDateLabelAlt = `${weekdayShort}, ${monthShort} ${Number.parseInt(day, 10)}, ${year}`;

  return [
    resolved,
    dateIso,
    dateSlashed,
    dateDotted,
    `${resolved}`,
    time12,
    time12Padded,
    time24,
    time12Compact,
    time12PaddedCompact,
    time12TitleCompact,
    time12PaddedTitleCompact,
    `${fullDateLabel} ${time12}`,
    `${fullDateLabelAlt} ${time12}`,
    `${monthDay} ${time12}`,
    `${monthDayShort} ${time12}`,
    `${weekdayLong} ${time12}`,
    `${weekdayShort} ${time12}`,
    `${dateIso} ${time12}`,
    `${dateIso} ${time24}`,
    `${dateIso} ${time12Compact}`,
    `${dateIso} ${time12PaddedCompact}`,
  ];
}

function extractSlotDateMeta(slot, timezone = SLOT_TIMEZONE) {
  const normalized = collapseWhitespace(String(slot));
  const resolved = convertSlotStringTimezone(normalized, SLOT_TIMEZONE, timezone) ?? normalized;
  const match = /^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)$/i.exec(resolved);
  if (!match) {
    return null;
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  const date = new Date(Date.UTC(year, month - 1, day));
  const monthLong = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    month: 'long',
  }).format(date);
  const monthShort = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    month: 'short',
  }).format(date);
  return {
    year,
    month,
    monthIndex: month - 1,
    day,
    dateIso: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
    monthLong,
    monthShort,
  };
}

function buildDateCandidates(slot, timezone = SLOT_TIMEZONE) {
  const normalized = collapseWhitespace(String(slot));
  const resolved = convertSlotStringTimezone(normalized, SLOT_TIMEZONE, timezone) ?? normalized;
  const match = /^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)$/i.exec(resolved);
  if (!match) {
    return [resolved];
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  const date = new Date(Date.UTC(year, month - 1, day));
  const monthLong = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    month: 'long',
    day: 'numeric',
  }).format(date);
  const monthShort = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    month: 'short',
    day: 'numeric',
  }).format(date);
  const weekdayLong = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    weekday: 'long',
  }).format(date);
  const weekdayShort = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    weekday: 'short',
  }).format(date);
  const dateIso = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  const dateNumeric = `${String(day)}`;
  const monthDay = `${monthLong}`;
  const monthDayShort = `${monthShort}`;

  return [
    resolved,
    dateIso,
    monthDay,
    `${monthDay}, ${weekdayLong}`,
    `${monthDay}, ${weekdayShort}`,
    monthDayShort,
    `${monthDayShort}, ${weekdayLong}`,
    `${monthDayShort}, ${weekdayShort}`,
    `${dateNumeric}, ${weekdayLong}`,
    `${dateNumeric}, ${weekdayShort}`,
    dateNumeric,
  ];
}

function convertSlotStringTimezone(slot, fromTimezone, toTimezone) {
  const normalized = collapseWhitespace(String(slot));
  const match = /^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)$/i.exec(normalized);
  if (!match) {
    return null;
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  const hour = Number.parseInt(match[4], 10);
  const minute = Number.parseInt(match[5], 10);
  const meridiem = match[6].toUpperCase();
  const hour24 = convertTo24Hour(hour, meridiem);

  const utcGuess = new Date(Date.UTC(year, month - 1, day, hour24, minute));
  const sourceUtc = localToUtcFromTimezone({
    year,
    month,
    day,
    hour24,
    minute,
    timezone: fromTimezone,
    guess: utcGuess,
  });
  const targetDate = new Date(sourceUtc.getTime());
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: toTimezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).formatToParts(targetDate);

  const outYear = parts.find((part) => part.type === 'year')?.value ?? '1970';
  const outMonth = parts.find((part) => part.type === 'month')?.value ?? '01';
  const outDay = parts.find((part) => part.type === 'day')?.value ?? '01';
  const outHour = parts.find((part) => part.type === 'hour')?.value ?? '12';
  const outMinute = parts.find((part) => part.type === 'minute')?.value ?? '00';
  const outMeridiem = parts.find((part) => part.type === 'dayPeriod')?.value ?? 'AM';
  return `${outYear}-${outMonth}-${outDay} ${Number.parseInt(outHour, 10)}:${outMinute} ${outMeridiem.toUpperCase()}`;
}

function localToUtcFromTimezone({ year, month, day, hour24, minute, timezone, guess }) {
  let current = guess ?? new Date(Date.UTC(year, month - 1, day, hour24, minute));

  for (let attempt = 0; attempt < 3; attempt += 1) {
    const offsetMinutes = getTimezoneOffsetMinutes(current, timezone);
    if (!Number.isFinite(offsetMinutes)) {
      return current;
    }
    const corrected = new Date(Date.UTC(year, month - 1, day, hour24, minute) - offsetMinutes * 60_000);
    if (Math.abs(corrected.getTime() - current.getTime()) < 60_000) {
      return corrected;
    }
    current = corrected;
  }

  return current;
}

function getTimezoneOffsetMinutes(date, timezone) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    timeZoneName: 'shortOffset',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(date);

  const zoneText = parts.find((part) => part.type === 'timeZoneName')?.value ?? '';
  const match = /GMT([+-])(\d{1,2})(?::?(\d{2}))?/i.exec(zoneText);
  if (!match) {
    return Number.NaN;
  }

  const sign = match[1] === '+' ? 1 : -1;
  const hours = Number.parseInt(match[2], 10);
  const minutes = Number.parseInt(match[3] ?? '0', 10);
  return sign * (hours * 60 + minutes);
}

function convertTo24Hour(hour, meridiem) {
  const normalized = Number.parseInt(String(hour), 10) % 12;
  if (meridiem === 'PM') {
    return normalized + 12;
  }
  return normalized;
}

function gmtOffsetToTimezone(offsetText) {
  const match = /^([+-])(\d{2}):(\d{2})$/.exec(String(offsetText ?? '').trim());
  if (!match) {
    return null;
  }

  const sign = match[1];
  const hours = Number.parseInt(match[2], 10);
  const minutes = Number.parseInt(match[3], 10);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes) || minutes !== 0) {
    return null;
  }

  if (sign === '+') {
    return `Etc/GMT-${hours}`;
  }

  return `Etc/GMT+${hours}`;
}

function getFrameDepth(frame) {
  let depth = 0;
  let current = frame;
  while (current.parentFrame()) {
    depth += 1;
    current = current.parentFrame();
  }
  return depth;
}

async function getTargetPage() {
  if (targetPage && !targetPage.isClosed()) {
    return targetPage;
  }

  targetPage = await (await getBrowserContext()).newPage();
  return targetPage;
}

function buildEvent(currentTarget, prev, curr, changedAt) {
  const prevSlots = Array.isArray(prev?.slots) ? prev.slots : [];
  const currSlots = Array.isArray(curr.slots) ? curr.slots : [];
  const prevStatus = prev?.status ?? null;

  if (curr.status === 'ERROR') {
    const prevErrorCount = Number.isFinite(prev?.errorCount) ? prev.errorCount : 0;
    const errorCount = prevStatus === 'ERROR' ? prevErrorCount + 1 : 1;
    if (errorCount < 2) {
      return null;
    }
    return {
      target: currentTarget.name,
      url: currentTarget.url,
      prevStatus,
      currStatus: curr.status,
      prevSlots,
      currSlots,
      changedAt,
      reason: 'error',
      detail: curr.reason ?? null,
      errorCount,
    };
  }

  if (!prev) {
    if (curr.status === 'OPEN') {
      return {
        target: currentTarget.name,
        url: currentTarget.url,
        prevStatus: null,
        currStatus: curr.status,
        prevSlots: [],
        currSlots,
        changedAt,
        reason: 'bootstrap_open',
        detail: curr.reason ?? null,
      };
    }
    return null;
  }

  if (prev.status !== curr.status) {
    return {
      target: currentTarget.name,
      url: currentTarget.url,
      prevStatus,
      currStatus: curr.status,
      prevSlots,
      currSlots,
      changedAt,
      reason: 'status_changed',
      detail: curr.reason ?? null,
    };
  }

  if (curr.status === 'OPEN' && !sameList(prevSlots, currSlots)) {
    return {
      target: currentTarget.name,
      url: currentTarget.url,
      prevStatus,
      currStatus: curr.status,
      prevSlots,
      currSlots,
      changedAt,
      reason: 'slots_changed',
      detail: curr.reason ?? null,
    };
  }

  return null;
}

function sameList(left, right) {
  if (left.length !== right.length) {
    return false;
  }

  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) {
      return false;
    }
  }

  return true;
}

function shouldTriggerAutofill({ triggerMode, prev, curr, targetRecord }) {
  const currentSignature = buildAutofillSignature(curr.status, curr.slots);
  const lastSignature = getTargetAutofillState(targetRecord)?.lastAutofillSignature ?? null;

  if (triggerMode === 'any_open_snapshot') {
    return currentSignature !== lastSignature;
  }

  if (triggerMode === 'open_change_only') {
    return prev?.status !== 'OPEN' || !sameList(prev?.slots ?? [], curr.slots ?? []);
  }

  return prev?.status !== 'OPEN' || !prev;
}

function buildAutofillSignature(status, slots) {
  return `${status}::${Array.isArray(slots) ? slots.join('|') : ''}`;
}

async function writeAlertFile(event) {
  if (
    !MONTJUIC_ALERT_FILE_PATH ||
    (event.currStatus !== 'OPEN' && !(CONFIRMATION_ALERT_ENABLED && event.currStatus === 'CONFIRMED'))
  ) {
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
    await fs.promises.mkdir(path.dirname(MONTJUIC_ALERT_FILE_PATH), { recursive: true }).catch(() => {});
    const tempPath = `${MONTJUIC_ALERT_FILE_PATH}.${process.pid}.${Date.now()}.tmp`;
    await fs.promises.writeFile(tempPath, `${summary}\n`, 'utf8');
    await fs.promises.rename(tempPath, MONTJUIC_ALERT_FILE_PATH);
  } catch (error) {
    console.log(
      `[MONTJUIC][WARN] unable to write alert file: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

async function pushToTelegram(event) {
  if (TELEGRAM_DISABLED || !TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
    return;
  }

  try {
    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
      body: new URLSearchParams({
        chat_id: TELEGRAM_CHAT_ID,
        text: formatTelegramMessage(event),
        disable_web_page_preview: 'true',
      }),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[MONTJUIC][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[MONTJUIC][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
    );
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

  return [
    `Montjuic 状态：${event.currStatus}`,
    `目标：${event.target}`,
    `原因：${event.reason}`,
    `时间：${event.changedAt}`,
    ...(event.prevStatus ? [`上次状态：${event.prevStatus}`] : []),
    ...(event.currStatus === 'OPEN' ? [`可预约时段：${slotSummary}`] : []),
    ...(event.currStatus === 'CONFIRMED' && event.detail ? [`确认内容：${event.detail}`] : []),
    `链接：${event.url}`,
  ].join('\n');
}

async function seedAlertFile() {
  if (!MONTJUIC_ALERT_FILE_PATH) {
    return;
  }

  const seedEvent = {
    target: 'montjuic',
    url: 'local-file-handoff',
    prevStatus: null,
    currStatus: 'UNKNOWN',
    prevSlots: [],
    currSlots: [],
    changedAt: new Date().toISOString(),
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
    await fs.promises.mkdir(path.dirname(MONTJUIC_ALERT_FILE_PATH), { recursive: true }).catch(() => {});
    const tempPath = `${MONTJUIC_ALERT_FILE_PATH}.${process.pid}.${Date.now()}.tmp`;
    await fs.promises.writeFile(tempPath, `${summary}\n`, 'utf8');
    await fs.promises.rename(tempPath, MONTJUIC_ALERT_FILE_PATH);
  } catch (error) {
    console.log(
      `[MONTJUIC][WARN] unable to seed alert file: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

async function writeMonitorHeartbeat(details) {
  const heartbeatPath = resolveMonitorPath(process.env.MONTJUIC_HEARTBEAT_FILE_PATH, 'montjuic_heartbeat.json');
  if (!heartbeatPath.trim()) {
    return;
  }

  const heartbeat = {
    process: 'montjuic_monitor.js',
    pid: process.pid,
    startedAt: monitorStartedAt,
    writtenAt: new Date().toISOString(),
    phase: details.phase,
    roundId: details.roundId ?? null,
    pollIntervalMs: POLL_INTERVAL_MS,
    pageTimeoutMs: PAGE_TIMEOUT_MS,
    monitorTimezone: MONITOR_TIMEZONE,
    slotTimezone: SLOT_TIMEZONE,
    monitorStartDate: MONITOR_START_DATE,
    monitorEndDate: MONITOR_END_DATE,
    targetName: target.name,
    profileCount: profiles.length,
  };

  try {
    await fs.promises.mkdir(path.dirname(heartbeatPath), { recursive: true }).catch(() => {});
    const tempPath = `${heartbeatPath}.${process.pid}.${Date.now()}.tmp`;
    await fs.promises.writeFile(tempPath, `${JSON.stringify(heartbeat, null, 2)}\n`, 'utf8');
    await fs.promises.rename(tempPath, heartbeatPath);
  } catch (error) {
    console.log(
      `[MONTJUIC][WARN] unable to write monitor heartbeat: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

function loadProfiles() {
  const csvProfiles = loadProfilesFromCsv();
  if (csvProfiles.length > 0) {
    return csvProfiles;
  }

  const raw = (process.env.MONTJUIC_PROFILES_JSON ?? '').trim();
  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const normalized = parsed
          .map((item, index) => normalizeProfile(item, index + 1))
          .filter(Boolean);
        if (normalized.length > 0) {
          return normalized;
        }
      }
    } catch (error) {
      console.log(
        `[MONTJUIC][WARN] unable to parse MONTJUIC_PROFILES_JSON: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }

  const fallback = normalizeProfile(
    {
      label: process.env.MONTJUIC_PROFILE_LABEL ?? 'default',
      surname: process.env.MONTJUIC_SURNAME ?? '',
      givenName: process.env.MONTJUIC_GIVEN_NAME ?? '',
      email: process.env.MONTJUIC_EMAIL ?? '',
      phone: process.env.MONTJUIC_PHONE ?? '',
      documentNumber: process.env.MONTJUIC_DOCUMENT_NUMBER ?? '',
      fullAddress: process.env.MONTJUIC_FULL_ADDRESS ?? '',
      postalCode: process.env.MONTJUIC_POSTAL_CODE ?? '',
      city: process.env.MONTJUIC_CITY ?? '',
      province: process.env.MONTJUIC_PROVINCE ?? '',
    },
    1,
  );

  return fallback ? [fallback] : [];
}

function loadProfilesFromCsv() {
  if (!PROFILES_CSV_PATH || !fs.existsSync(PROFILES_CSV_PATH)) {
    return [];
  }

  try {
    const raw = fs.readFileSync(PROFILES_CSV_PATH, 'utf8');
    const rows = parseCsv(raw);
    if (!rows.length) {
      return [];
    }

    const [header, ...dataRows] = rows;
    const headerIndex = new Map(header.map((column, index) => [column.trim(), index]));
    const normalized = dataRows
      .map((row, index) => csvRowToProfile(row, headerIndex, index + 1))
      .filter(Boolean);
    return normalized;
  } catch (error) {
    console.log(
      `[MONTJUIC][WARN] unable to parse CSV profiles: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    return [];
  }
}

function csvRowToProfile(row, headerIndex, fallbackIndex) {
  const get = (...names) => {
    for (const name of names) {
      const index = headerIndex.get(name);
      if (Number.isInteger(index)) {
        return normalizeText(row[index] ?? '');
      }
    }
    return '';
  };

  const profile = {
    label: get('label', 'name') || `profile-${String(fallbackIndex).padStart(3, '0')}`,
    surname: get('surname', 'last_name', 'lastname', 'apellido'),
    givenName: get('givenName', 'given_name', 'first_name', 'firstname', 'nombre'),
    email: get('email', 'mail', 'correo'),
    phone: get('phone', 'telephone', 'telefono', 'tel'),
    fullAddress: get('fullAddress', 'address', 'direccion', 'dirección completa'),
    documentNumber: get('documentNumber', 'document', 'numeroDocumento', 'numero_de_documento'),
    nationality: get('nationality', 'country', 'pais', 'nacionalidad'),
    birthDate: get('birthDate', 'dateOfBirth', 'dob', 'fechaNacimiento'),
  };

  const hasAnyField = Object.entries(profile).some(([key, value]) => key !== 'label' && value);
  return hasAnyField ? profile : null;
}

function normalizeProfile(raw, fallbackIndex) {
  if (!raw || typeof raw !== 'object') {
    return null;
  }

  const profile = {
    label: normalizeText(raw.label ?? raw.name ?? raw.profile ?? `profile-${fallbackIndex}`),
    surname: normalizeText(raw.surname ?? raw.lastName ?? raw.familyName ?? raw.apellido),
    givenName: normalizeText(raw.givenName ?? raw.firstName ?? raw.nombre),
    email: normalizeText(raw.email ?? raw.mail ?? raw.correo),
    phone: normalizeText(raw.phone ?? raw.telefono ?? raw.tel),
    documentNumber: normalizeText(raw.documentNumber ?? raw.document ?? raw.numeroDocumento ?? raw.passport),
    fullAddress: normalizeText(raw.fullAddress ?? raw.address ?? raw.direccion),
    nationality: normalizeText(raw.nationality ?? raw.country ?? raw.nacionalidad ?? raw.pais),
    birthDate: normalizeText(raw.birthDate ?? raw.dateOfBirth ?? raw.dob ?? raw.fechaNacimiento),
  };

  const hasAnyField = Object.entries(profile).some(([key, value]) => key !== 'label' && value);
  return hasAnyField ? profile : null;
}

function normalizeText(value) {
  return String(value ?? '').trim();
}

function parseCsv(raw) {
  const rows = [];
  let currentRow = [];
  let currentValue = '';
  let inQuotes = false;

  for (let index = 0; index < raw.length; index += 1) {
    const char = raw[index];
    const nextChar = raw[index + 1];

    if (char === '"' && inQuotes && nextChar === '"') {
      currentValue += '"';
      index += 1;
      continue;
    }

    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (char === ',' && !inQuotes) {
      currentRow.push(currentValue);
      currentValue = '';
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && nextChar === '\n') {
        index += 1;
      }
      currentRow.push(currentValue);
      if (currentRow.some((cell) => String(cell).trim() !== '')) {
        rows.push(currentRow);
      }
      currentRow = [];
      currentValue = '';
      continue;
    }

    currentValue += char;
  }

  currentRow.push(currentValue);
  if (currentRow.some((cell) => String(cell).trim() !== '')) {
    rows.push(currentRow);
  }

  return rows;
}

function normalizeDateValue(value) {
  const text = collapseWhitespace(value);
  const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (isoMatch) {
    return text;
  }

  const slashMatch = /^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})$/.exec(text);
  if (!slashMatch) {
    return text;
  }

  const first = Number.parseInt(slashMatch[1], 10);
  const second = Number.parseInt(slashMatch[2], 10);
  const year = slashMatch[3].length === 2 ? Number.parseInt(`20${slashMatch[3]}`, 10) : Number.parseInt(slashMatch[3], 10);
  const day = first > 12 ? first : second;
  const month = first > 12 ? second : first;
  return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

async function selectOptionByValueOrLabel(locator, value) {
  const text = String(value ?? '').trim();
  if (!text) {
    return;
  }

  try {
    await locator.selectOption({ label: text });
    return;
  } catch {
    // try values below
  }

  try {
    await locator.selectOption({ value: text });
    return;
  } catch {
    // try normalized fallback
  }

  const normalized = text.toLowerCase();
  await locator.selectOption({ label: normalized }).catch(() => {});
}

async function verifyFilledValue(locator, expectedValue, key) {
  const actual = await readFieldValue(locator, key);
  const expected = normalizeComparableValue(expectedValue, key);
  return actual === expected || (expected && actual.includes(expected));
}

async function readFieldValue(locator, key) {
  const tagName = await locator.evaluate((element) => element.tagName.toLowerCase()).catch(() => 'input');
  if (tagName === 'select') {
    const selectInfo = await locator.evaluate((element) => {
      const select = element;
      const option = select.selectedOptions?.[0];
      return {
        value: select.value ?? '',
        label: option?.label ?? option?.textContent ?? '',
      };
    }).catch(() => ({ value: '', label: '' }));
    return normalizeComparableValue(selectInfo.label || selectInfo.value, key);
  }

  if (key === 'birthDate') {
    return normalizeComparableValue(await locator.inputValue().catch(() => ''), key);
  }

  if (tagName === 'textarea' || tagName === 'input' || tagName === 'div') {
    return normalizeComparableValue(await locator.inputValue().catch(() => ''), key);
  }

  return normalizeComparableValue(await locator.textContent().catch(() => ''), key);
}

function normalizeComparableValue(value, key) {
  const text = collapseWhitespace(value);
  if (key === 'birthDate') {
    return normalizeDateValue(text);
  }
  return text;
}

function collapseWhitespace(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function isFullText(text) {
  const lowered = String(text).toLowerCase();
  return [
    'no hay horas disponibles',
    'no hay disponibilidad',
    'no hours available',
    'no available hours',
    'no availability',
    'no availability during these days',
    'no hay horas',
  ].some((phrase) => lowered.includes(phrase));
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function uniqueAndSortSlots(slots) {
  return [...new Set(slots)].sort((a, b) => a.localeCompare(b));
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
    console.log(
      `[MONTJUIC][WARN] unable to read state file: ${error instanceof Error ? error.message : String(error)}`,
    );
    return { targets: {} };
  }
}

function saveState(filePath, data) {
  const tempPath = `${filePath}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  fs.renameSync(tempPath, filePath);
}

function getTargetRecord(snapshots, targetName) {
  const existing = snapshots.get(targetName);
  if (existing && typeof existing === 'object') {
    if ('current' in existing) {
      if (!('autofill' in existing)) {
        existing.autofill = null;
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
      autofill: null,
    };
    snapshots.set(targetName, migrated);
    return migrated;
  }

  const created = {
    autofill: null,
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

function getTargetAutofillState(targetRecord) {
  return targetRecord.autofill ?? null;
}

function setTargetAutofillState(targetRecord, nextState) {
  targetRecord.autofill = nextState;
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
    const value = trimmed.slice(equalsIndex + 1).trim();
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

function resolveMonitorPath(value, fallbackName) {
  const raw = String(value ?? '').trim();
  if (!raw) {
    return path.join(__dirname, fallbackName);
  }

  if (path.isAbsolute(raw)) {
    return raw;
  }

  return path.join(__dirname, raw);
}

function readInteger(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === null || String(raw).trim() === '') {
    return fallback;
  }

  const parsed = Number.parseInt(String(raw).trim(), 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function hashContent(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exitCode = 1;
});
