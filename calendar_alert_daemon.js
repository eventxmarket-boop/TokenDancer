#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvFile(path.join(__dirname, '.env'));

const ALERT_FILE_PATH = (process.env.ALERT_FILE_PATH ?? '/Users/chanzi/.qclaw/workspace-agent-be2ecf0c/calendar_alert.txt').trim();
const ALERT_DAEMON_POLL_MS = readInteger('ALERT_DAEMON_POLL_MS', 250);
const ALERT_DAEMON_DEBOUNCE_MS = readInteger('ALERT_DAEMON_DEBOUNCE_MS', 120);
const FORWARD_ALL_STATUSES = (process.env.FORWARD_ALL_STATUSES ?? 'false').toLowerCase() === 'true';
const NOTIFY_WEBHOOK_URL = (process.env.NOTIFY_WEBHOOK_URL ?? '').trim();
const NOTIFY_WEBHOOK_SECRET = (process.env.NOTIFY_WEBHOOK_SECRET ?? '').trim();

const stopSignals = new Set();
let lastHash = null;
let pendingTimer = null;
let processing = false;
let queued = false;

process.on('SIGINT', () => {
  stopSignals.add('SIGINT');
});

process.on('SIGTERM', () => {
  stopSignals.add('SIGTERM');
});

async function main() {
  if (!ALERT_FILE_PATH) {
    throw new Error('ALERT_FILE_PATH is required');
  }

  console.log(`[DAEMON] watching ${ALERT_FILE_PATH}`);
  await seedBaseline();

  fs.watchFile(ALERT_FILE_PATH, { interval: ALERT_DAEMON_POLL_MS }, () => {
    scheduleProcess();
  });

  scheduleProcess();

  while (!stopSignals.size) {
    await sleep(1000);
  }

  fs.unwatchFile(ALERT_FILE_PATH);
}

function scheduleProcess() {
  queued = true;
  if (pendingTimer) {
    return;
  }

  pendingTimer = setTimeout(() => {
    pendingTimer = null;
    void drainQueue();
  }, ALERT_DAEMON_DEBOUNCE_MS);
}

async function drainQueue() {
  if (processing) {
    scheduleProcess();
    return;
  }

  processing = true;
  try {
    while (queued && !stopSignals.size) {
      queued = false;
      await processAlertFile();
    }
  } finally {
    processing = false;
  }
}

async function seedBaseline() {
  if (!fs.existsSync(ALERT_FILE_PATH)) {
    console.log('[DAEMON] alert file missing, waiting');
    return;
  }

  try {
    const content = await fs.promises.readFile(ALERT_FILE_PATH, 'utf8');
    lastHash = hashContent(content);
    console.log(`[DAEMON] baseline loaded | hash=${lastHash}`);
  } catch (error) {
    console.log(`[DAEMON] baseline read failed | ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function processAlertFile() {
  try {
    const content = await fs.promises.readFile(ALERT_FILE_PATH, 'utf8');
    const hash = hashContent(content);

    if (hash === lastHash) {
      console.log('hash unchanged, skip');
      return;
    }

    const parsed = parseAlertFile(content);
    if (!parsed) {
      console.log('[DAEMON] parse failed, keeping previous baseline');
      return;
    }

    if (!FORWARD_ALL_STATUSES && parsed.currStatus !== 'OPEN' && parsed.currStatus !== 'ERROR') {
      console.log(`状态为 ${parsed.currStatus}，非 OPEN/ERROR，不推送。静默退出。`);
      lastHash = hash;
      return;
    }

    const event = {
      target: parsed.target,
      url: parsed.url,
      prevStatus: parsed.prevStatus ?? null,
      currStatus: parsed.currStatus ?? null,
      prevSlots: Array.isArray(parsed.prevSlots) ? parsed.prevSlots : [],
      currSlots: Array.isArray(parsed.currSlots) ? parsed.currSlots : [],
      changedAt: parsed.changedAt ?? new Date().toISOString(),
      reason: parsed.reason ?? 'unknown',
    };

    console.log(`EVENT_JSON:${JSON.stringify(event)}`);
    if (NOTIFY_WEBHOOK_URL) {
      await postWebhook(event);
    }

    lastHash = hash;
    console.log('HEARTBEAT_OK');
  } catch (error) {
    console.log(`[DAEMON] read error | ${error instanceof Error ? error.message : String(error)}`);
  }
}

function parseAlertFile(content) {
  const lines = content.split(/\r?\n/);
  const jsonLine = [...lines].reverse().find((line) => line.trim().startsWith('{'));
  if (!jsonLine) {
    return null;
  }

  try {
    const payload = JSON.parse(jsonLine);
    return {
      target: payload.target,
      url: payload.url,
      prevStatus: payload.prevStatus,
      currStatus: payload.currStatus,
      prevSlots: payload.prevSlots,
      currSlots: payload.currSlots,
      changedAt: payload.changedAt,
      reason: payload.reason,
    };
  } catch {
    return null;
  }
}

async function postWebhook(event) {
  const headers = { 'Content-Type': 'application/json' };
  if (NOTIFY_WEBHOOK_SECRET) {
    headers['X-Webhook-Secret'] = NOTIFY_WEBHOOK_SECRET;
  }

  const response = await fetch(NOTIFY_WEBHOOK_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify(event),
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    console.log(
      `[DAEMON] webhook failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
    );
  }
}

function hashContent(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
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

await main();
