#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvFile(path.join(__dirname, '.env'));

const HEARTBEAT_FILE_PATH = (process.env.MONITOR_HEARTBEAT_FILE_PATH ?? path.join(__dirname, 'monitor_heartbeat.json')).trim();
const ALERT_FILE_PATH = (process.env.ALERT_FILE_PATH ?? '').trim();
const HEALTH_STATE_FILE = path.join(__dirname, process.env.MONITOR_HEALTH_STATE_FILE ?? 'monitor_health_state.json');
const HEALTH_CHECK_INTERVAL_MS = readInteger('MONITOR_HEALTH_CHECK_INTERVAL_MS', 60_000);
const HEALTH_STALE_AFTER_MS = readInteger('MONITOR_HEALTH_STALE_AFTER_MS', 720_000);
const HEALTH_STARTUP_GRACE_MS = readInteger('MONITOR_HEALTH_STARTUP_GRACE_MS', 120_000);
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();

const startedAtMs = Date.now();
const stopSignals = new Set();
let currentState = loadHealthState();
let lastCheckAt = null;
let corruptStreak = currentState.corruptStreak ?? 0;

process.on('SIGINT', () => {
  stopSignals.add('SIGINT');
});

process.on('SIGTERM', () => {
  stopSignals.add('SIGTERM');
});

async function main() {
  if (!ALERT_FILE_PATH && (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID)) {
    throw new Error('ALERT_FILE_PATH is required');
  }

  console.log(`[HEALTH] watching ${HEARTBEAT_FILE_PATH}`);
  await evaluateHealth({ initial: true });

  while (!stopSignals.size) {
    await sleep(HEALTH_CHECK_INTERVAL_MS);
    if (stopSignals.size) {
      break;
    }

    await evaluateHealth({ initial: false });
  }
}

async function evaluateHealth({ initial }) {
  lastCheckAt = new Date().toISOString();
  const snapshot = await readHeartbeatSnapshot();

  if (!snapshot.exists) {
    const daemonAgeMs = Date.now() - startedAtMs;
    if (daemonAgeMs < HEALTH_STARTUP_GRACE_MS) {
      console.log(`[HEALTH] waiting for heartbeat file | graceMs=${HEALTH_STARTUP_GRACE_MS}`);
      return;
    }

    await maybeAlert({
      reason: 'heartbeat_missing',
      snapshot: null,
      ageMs: null,
      initial,
    });
    return;
  }

  if (snapshot.parseError) {
    corruptStreak += 1;
    currentState = {
      ...currentState,
      corruptStreak,
    };
    saveHealthState(currentState);

    if (corruptStreak < 2) {
      console.log(`[HEALTH] transient corrupt read ignored | streak=${corruptStreak}/2`);
      return;
    }

    await maybeAlert({
      reason: 'heartbeat_corrupt',
      snapshot,
      ageMs: null,
      initial,
    });
    return;
  }

  const ageMs = Math.max(0, Date.now() - snapshot.stat.mtimeMs);
  if (ageMs <= HEALTH_STALE_AFTER_MS) {
    corruptStreak = 0;
    if (currentState.incidentActive) {
      console.log(
        `[HEALTH] recovered | ageMs=${ageMs} | phase=${snapshot.payload?.phase ?? 'unknown'} | writtenAt=${snapshot.payload?.writtenAt ?? snapshot.stat.mtimeIso}`,
      );
    } else {
      console.log(
        `[HEALTH] ok | ageMs=${ageMs} | phase=${snapshot.payload?.phase ?? 'unknown'} | writtenAt=${snapshot.payload?.writtenAt ?? snapshot.stat.mtimeIso}`,
      );
    }

    currentState = {
      incidentActive: false,
      lastReason: null,
      lastAlertAt: currentState.lastAlertAt ?? null,
      lastRecoveredAt: new Date().toISOString(),
      corruptStreak: 0,
    };
    saveHealthState(currentState);
    return;
  }

  await maybeAlert({
    reason: 'heartbeat_stale',
    snapshot,
    ageMs,
    initial,
  });
}

async function maybeAlert({ reason, snapshot, ageMs, initial }) {
  if (currentState.incidentActive) {
    console.log(
      `[HEALTH] still unhealthy | reason=${reason} | ageMs=${ageMs ?? 'n/a'} | initial=${initial ? 'true' : 'false'}`,
    );
    return;
  }

  const now = new Date().toISOString();
  const event = {
    target: 'monitor-health',
    url: 'heartbeat://monitor.js',
    prevStatus: 'UNKNOWN',
    currStatus: 'ERROR',
    prevSlots: [],
    currSlots: [],
    changedAt: now,
    reason,
    heartbeatFile: HEARTBEAT_FILE_PATH,
    heartbeatWrittenAt: snapshot?.payload?.writtenAt ?? null,
    heartbeatMtime: snapshot?.stat?.mtimeIso ?? null,
    heartbeatAgeMs: ageMs,
    monitorPid: snapshot?.payload?.pid ?? null,
    monitorPhase: snapshot?.payload?.phase ?? null,
    monitorRoundId: snapshot?.payload?.roundId ?? null,
  };

  await pushToTelegram(event);
  if (ALERT_FILE_PATH) {
    await writeAlertFile(event);
  }
  currentState = {
    incidentActive: true,
    lastReason: reason,
    lastAlertAt: now,
    lastRecoveredAt: currentState.lastRecoveredAt ?? null,
    corruptStreak,
  };
  saveHealthState(currentState);

  console.log(`EVENT_JSON:${JSON.stringify(event)}`);
  console.log(`[HEALTH] alert emitted | reason=${reason} | ageMs=${ageMs ?? 'n/a'}`);
}

async function pushToTelegram(event) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
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
        text: [
          '监控健康异常',
          `reason=${event.reason}`,
          `heartbeatFile=${event.heartbeatFile ?? '-'}`,
          `ageMs=${event.heartbeatAgeMs ?? '-'}`,
          `monitorPid=${event.monitorPid ?? '-'}`,
        ].join('\n'),
        disable_web_page_preview: 'true',
      }),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[HEALTH][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[HEALTH][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

async function readHeartbeatSnapshot() {
  try {
    const stat = await fs.promises.stat(HEARTBEAT_FILE_PATH);
    const content = await fs.promises.readFile(HEARTBEAT_FILE_PATH, 'utf8');

    try {
      const payload = JSON.parse(content);
      return {
        exists: true,
        stat: {
          mtimeMs: stat.mtimeMs,
          mtimeIso: new Date(stat.mtimeMs).toISOString(),
        },
        payload,
        parseError: null,
      };
    } catch (error) {
      return {
        exists: true,
        stat: {
          mtimeMs: stat.mtimeMs,
          mtimeIso: new Date(stat.mtimeMs).toISOString(),
        },
        payload: null,
        parseError: error instanceof Error ? error.message : String(error),
      };
    }
  } catch (error) {
    if (error instanceof Error && 'code' in error && error.code === 'ENOENT') {
      return {
        exists: false,
        stat: null,
        payload: null,
        parseError: null,
      };
    }

    throw error;
  }
}

async function writeAlertFile(event) {
  const summary = [
    `target=${event.target}`,
    `status=${event.currStatus}`,
    `reason=${event.reason}`,
    `changedAt=${event.changedAt}`,
    `slots=`,
    `url=${event.url}`,
    `heartbeatFile=${event.heartbeatFile ?? ''}`,
    `heartbeatWrittenAt=${event.heartbeatWrittenAt ?? ''}`,
    `heartbeatMtime=${event.heartbeatMtime ?? ''}`,
    `heartbeatAgeMs=${event.heartbeatAgeMs ?? ''}`,
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
      `[HEALTH] unable to write alert file | ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

function loadHealthState() {
  try {
    if (!fs.existsSync(HEALTH_STATE_FILE)) {
      return {
        incidentActive: false,
        lastReason: null,
        lastAlertAt: null,
        lastRecoveredAt: null,
        corruptStreak: 0,
      };
    }

    const parsed = JSON.parse(fs.readFileSync(HEALTH_STATE_FILE, 'utf8'));
    if (!parsed || typeof parsed !== 'object') {
      return {
        incidentActive: false,
        lastReason: null,
        lastAlertAt: null,
        lastRecoveredAt: null,
        corruptStreak: 0,
      };
    }

    return {
      incidentActive: Boolean(parsed.incidentActive),
      lastReason: typeof parsed.lastReason === 'string' ? parsed.lastReason : null,
      lastAlertAt: typeof parsed.lastAlertAt === 'string' ? parsed.lastAlertAt : null,
      lastRecoveredAt: typeof parsed.lastRecoveredAt === 'string' ? parsed.lastRecoveredAt : null,
      corruptStreak: Number.isFinite(parsed.corruptStreak) ? parsed.corruptStreak : 0,
    };
  } catch (error) {
    console.log(`[HEALTH] unable to read state file | ${error instanceof Error ? error.message : String(error)}`);
    return {
      incidentActive: false,
      lastReason: null,
      lastAlertAt: null,
      lastRecoveredAt: null,
      corruptStreak: 0,
    };
  }
}

function saveHealthState(state) {
  try {
    const tempPath = `${HEALTH_STATE_FILE}.${process.pid}.${Date.now()}.${randomUUID()}.tmp`;
    fs.writeFileSync(tempPath, `${JSON.stringify(state, null, 2)}\n`, 'utf8');
    fs.renameSync(tempPath, HEALTH_STATE_FILE);
  } catch (error) {
    console.log(`[HEALTH] unable to save state | ${error instanceof Error ? error.message : String(error)}`);
  }
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

function readInteger(name, fallback) {
  const value = Number.parseInt(process.env[name] ?? '', 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

await main().catch((error) => {
  console.error(`[FATAL] ${error instanceof Error ? error.stack || error.message : String(error)}`);
  process.exitCode = 1;
});
