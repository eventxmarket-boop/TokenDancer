#!/usr/bin/env node

const Z_TO_MONTJUIC_ENV_MAP = new Map([
  ['Z_CHAIN_TARGET_NAME', 'MONTJUIC_TARGET_NAME'],
  ['Z_CHAIN_TARGET_URL', 'MONTJUIC_TARGET_URL'],
  ['Z_CHAIN_PROFILES_CSV_PATH', 'MONTJUIC_PROFILES_CSV_PATH'],
  ['Z_CHAIN_PROFILES_JSON', 'MONTJUIC_PROFILES_JSON'],
  ['Z_CHAIN_POLL_INTERVAL_MS', 'MONTJUIC_POLL_INTERVAL_MS'],
  ['Z_CHAIN_PAGE_TIMEOUT_MS', 'MONTJUIC_PAGE_TIMEOUT_MS'],
  ['Z_CHAIN_PAGE_GOTO_DELAY_MS', 'MONTJUIC_PAGE_GOTO_DELAY_MS'],
  ['Z_CHAIN_CLICK_SETTLE_MS', 'MONTJUIC_CLICK_SETTLE_MS'],
  ['Z_CHAIN_HEADLESS', 'MONTJUIC_HEADLESS'],
  ['Z_CHAIN_TIMEZONE', 'MONTJUIC_TIMEZONE'],
  ['Z_CHAIN_SLOT_TIMEZONE', 'MONTJUIC_SLOT_TIMEZONE'],
  ['Z_CHAIN_ALERT_FILE_PATH', 'MONTJUIC_ALERT_FILE_PATH'],
  ['Z_CHAIN_SIGNAL_FILE_PATH', 'MONTJUIC_SIGNAL_FILE_PATH'],
  ['Z_CHAIN_STATE_FILE', 'MONTJUIC_STATE_FILE'],
  ['Z_CHAIN_HEARTBEAT_FILE_PATH', 'MONTJUIC_HEARTBEAT_FILE_PATH'],
  ['Z_CHAIN_AUTO_SUBMIT', 'MONTJUIC_AUTO_SUBMIT'],
  ['Z_CHAIN_BATCH_LIMIT', 'MONTJUIC_BATCH_LIMIT'],
  ['Z_CHAIN_CONFIRMATION_ALERT_ENABLED', 'MONTJUIC_CONFIRMATION_ALERT_ENABLED'],
  ['Z_CHAIN_AUTOFILL_TRIGGER_MODE', 'MONTJUIC_AUTOFILL_TRIGGER_MODE'],
]);

for (const [sourceKey, targetKey] of Z_TO_MONTJUIC_ENV_MAP.entries()) {
  const sourceValue = process.env[sourceKey];
  if (typeof sourceValue === 'string' && sourceValue.trim()) {
    process.env[targetKey] = sourceValue;
  }
}

const chainInstanceId = sanitizeChainInstanceId(
  process.env.Z_CHAIN_INSTANCE_ID ?? process.env.Z_CHAIN_TARGET_NAME ?? 'z-chain',
);
const chainBaseDir = process.env.Z_CHAIN_BASE_DIR?.trim() || `${process.env.HOME ?? '/Users/chanzi'}/.qclaw/workspace-agent-be2ecf0c`;
if (!process.env.MONTJUIC_ALERT_FILE_PATH) {
  process.env.MONTJUIC_ALERT_FILE_PATH = `${chainBaseDir}/${chainInstanceId}_alert.txt`;
}
if (!process.env.MONTJUIC_SIGNAL_FILE_PATH) {
  process.env.MONTJUIC_SIGNAL_FILE_PATH = process.env.MONTJUIC_ALERT_FILE_PATH;
}
if (!process.env.MONTJUIC_STATE_FILE) {
  process.env.MONTJUIC_STATE_FILE = `${chainBaseDir}/${chainInstanceId}_executor_state.json`;
}
if (!process.env.MONTJUIC_HEARTBEAT_FILE_PATH) {
  process.env.MONTJUIC_HEARTBEAT_FILE_PATH = `${chainBaseDir}/${chainInstanceId}_executor_heartbeat.json`;
}

if (!process.env.MONTJUIC_TARGET_URL?.trim()) {
  console.error('[Z_CHAIN_EXECUTOR] MONTJUIC_TARGET_URL is required (set Z_CHAIN_TARGET_URL first)');
  await new Promise(() => {});
}

if (!process.env.MONTJUIC_CONSUMER_MODE) {
  process.env.MONTJUIC_CONSUMER_MODE = 'true';
}

if (!process.env.MONTJUIC_EXECUTION_ONLY) {
  process.env.MONTJUIC_EXECUTION_ONLY = 'true';
}

if (!process.env.MONTJUIC_CONFIRMATION_ALERT_ENABLED) {
  process.env.MONTJUIC_CONFIRMATION_ALERT_ENABLED = 'true';
}

if (!process.env.MONTJUIC_SUPPRESS_STATUS_EVENTS) {
  process.env.MONTJUIC_SUPPRESS_STATUS_EVENTS = 'true';
}

if (!process.env.MONTJUIC_AUTO_SUBMIT) {
  process.env.MONTJUIC_AUTO_SUBMIT = 'true';
}

if (!process.env.MONITOR_LANE_START_OFFSETS_MS) {
  process.env.MONITOR_LANE_START_OFFSETS_MS = '0';
}

if (!process.env.MONITOR_LANE_INTERVAL_MS) {
  process.env.MONITOR_LANE_INTERVAL_MS = process.env.Z_CHAIN_POLL_INTERVAL_MS?.trim() || '5000';
}

await import('./montjuic_monitor.js');

function sanitizeChainInstanceId(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '') || 'z-chain';
}
