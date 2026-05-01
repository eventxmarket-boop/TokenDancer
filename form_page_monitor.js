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

const TARGETS = loadFormTargets();
const POLL_INTERVAL_MS = readInteger('FORM_PAGE_POLL_INTERVAL_MS', 60_000);
const LANE_INTERVAL_MS = readInteger('MONITOR_LANE_INTERVAL_MS', POLL_INTERVAL_MS);
const LANE_START_OFFSETS_MS = parseLaneOffsets(process.env.MONITOR_LANE_START_OFFSETS_MS);
const PAGE_TIMEOUT_MS = readInteger('FORM_PAGE_PAGE_TIMEOUT_MS', 30_000);
const PAGE_STABILIZE_MS = readInteger('FORM_PAGE_PAGE_STABILIZE_MS', 2_000);
const HEADLESS = (process.env.FORM_PAGE_HEADLESS ?? 'true').toLowerCase() !== 'false';
const ALERT_FILE_PATH = (process.env.FORM_PAGE_ALERT_FILE_PATH ?? '').trim();
const FALLBACK_ALERT_FILE_PATH = path.join(__dirname, 'form_page_alert.txt');
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const STATE_FILE = path.join(__dirname, process.env.FORM_PAGE_STATE_FILE ?? 'form_page_state.json');
const STATE_VERSION = 4;
const monitorStartedAt = new Date().toISOString();
if (!TARGETS.length) {
  throw new Error('No FORM_PAGE targets configured');
}

const stopSignals = new Set();
let browser = null;
let context = null;

process.on('SIGINT', () => {
  stopSignals.add('SIGINT');
});

process.on('SIGTERM', () => {
  stopSignals.add('SIGTERM');
});

async function main() {
  browser = await chromium.launch({ headless: HEADLESS });
  context = await browser.newContext();

  try {
    const state = loadState();

    await runSerializedLaneScheduler({
      laneStartOffsetsMs: LANE_START_OFFSETS_MS,
      laneIntervalMs: LANE_INTERVAL_MS,
      stopSignals,
      onLaneStart: ({ laneIndex, offsetMs }) => {
        console.log(
          `[FORM_PAGE] lane start | lane=${laneIndex} | offsetMs=${offsetMs} | targets=${TARGETS.length}`,
        );
      },
      onTick: async ({ laneIndex, cycle }) => {
        const roundStartedAt = new Date().toISOString();
        console.log(
          `[FORM_PAGE] lane #${laneIndex} cycle #${cycle} start | targets=${TARGETS.length} | at=${roundStartedAt}`,
        );

        for (const target of TARGETS) {
          const snapshot = await probeFormPage(target);
          const previous = state.targets[target.key] ?? null;
          const currentHash = snapshot.hash;
          const previousHash = previous?.hash ?? null;
          const previousStateVersion = Number.isFinite(previous?.stateVersion) ? previous.stateVersion : 0;
          const stateMismatch = previousStateVersion !== STATE_VERSION;
          const shouldSuppressUpdate = shouldSuppressFormUpdate(target, snapshot);

          if (!previousHash || stateMismatch) {
            state.targets[target.key] = {
              key: target.key,
              name: target.name,
              url: target.url,
              resolvedUrl: snapshot.resolvedUrl,
              hash: currentHash,
              title: snapshot.title,
              excerpt: snapshot.excerpt,
              updatedAt: roundStartedAt,
              stateVersion: STATE_VERSION,
              monitorStartedAt,
            };
            saveState(STATE_FILE, state);
            console.log(
              `[FORM_PAGE] baseline seeded | target=${target.name} | hash=${currentHash}` +
                (stateMismatch ? ' | reseeded=true' : ''),
            );
            continue;
          }

          if (previousHash !== currentHash) {
            if (shouldSuppressUpdate) {
              state.targets[target.key] = {
                key: target.key,
                name: target.name,
                url: target.url,
                resolvedUrl: snapshot.resolvedUrl,
                hash: currentHash,
                title: snapshot.title,
                excerpt: snapshot.excerpt,
                updatedAt: roundStartedAt,
                stateVersion: STATE_VERSION,
                monitorStartedAt,
              };
              saveState(STATE_FILE, state);
              console.log(
                `[FORM_PAGE] alias drift ignored | target=${target.name} | resolvedUrl=${snapshot.resolvedUrl || '-'}`,
              );
              continue;
            }

            const changedAt = new Date().toISOString();
            const event = {
              target: target.name,
              url: target.url,
              resolvedUrl: snapshot.resolvedUrl,
              prevStatus: 'STABLE',
              currStatus: 'UPDATED',
              prevSlots: previous?.excerpt ? [previous.excerpt] : [],
              currSlots: [snapshot.excerpt],
              changedAt,
              reason: 'page_updated',
            };

            const summary = [
              '你监控的页面发生了更新',
              `target=${target.name}`,
              `url=${target.url}`,
              `resolvedUrl=${snapshot.resolvedUrl || '-'}`,
              `changedAt=${changedAt}`,
              `title=${snapshot.title || '-'}`,
              `excerpt=${snapshot.excerpt || '-'}`,
              '',
              JSON.stringify(event),
            ].join('\n');

            console.log(`EVENT_JSON:${JSON.stringify(event)}`);
            void pushToTelegram(event);
            await writeAlertFile(summary);

            state.targets[target.key] = {
              key: target.key,
              name: target.name,
              url: target.url,
              resolvedUrl: snapshot.resolvedUrl,
              hash: currentHash,
              title: snapshot.title,
              excerpt: snapshot.excerpt,
              updatedAt: changedAt,
              stateVersion: STATE_VERSION,
              monitorStartedAt,
            };
            saveState(STATE_FILE, state);
          } else {
            state.targets[target.key] = {
              key: target.key,
              name: target.name,
              url: target.url,
              resolvedUrl: snapshot.resolvedUrl,
              hash: currentHash,
              title: snapshot.title,
              excerpt: snapshot.excerpt,
              updatedAt: previous?.updatedAt ?? roundStartedAt,
              stateVersion: previous?.stateVersion ?? STATE_VERSION,
              monitorStartedAt,
            };
            saveState(STATE_FILE, state);
            console.log(`[FORM_PAGE] unchanged | target=${target.name} | hash=${currentHash}`);
          }
        }
      },
    });
  } finally {
    if (context) {
      await context.close().catch(() => {});
    }
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function probeFormPage(target) {
  if (!target?.url) {
    return {
      hash: hashContent('missing_url'),
      title: '',
      excerpt: 'missing_url',
      resolvedUrl: '',
    };
  }

  try {
    const page = await context.newPage();
    try {
      page.setDefaultTimeout(PAGE_TIMEOUT_MS);
      page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

      await page.goto(target.url, { waitUntil: 'domcontentloaded', timeout: PAGE_TIMEOUT_MS });
      await page.waitForTimeout(PAGE_STABILIZE_MS);

      const snapshot = await page.evaluate(() => {
        const title = (document.title ?? '').trim();
        const bodyText = (document.body?.innerText ?? '').replace(/\s+/g, ' ').trim();
        return { title, bodyText };
      });
      const resolvedUrl = page.url().trim();

      const normalized = normalizeSnapshot(snapshot.title, snapshot.bodyText);
      return {
        hash: hashContent(normalized),
        title: snapshot.title,
        excerpt: makeExcerpt(snapshot.bodyText, snapshot.title, resolvedUrl),
        resolvedUrl,
      };
    } finally {
      await page.close().catch(() => {});
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`[FORM_PAGE][ERROR] target=${target?.name ?? 'unknown'} | ${message}`);
    return {
      hash: hashContent(`error:${message}`),
      title: '',
      excerpt: message,
      resolvedUrl: '',
    };
  }
}

function normalizeSnapshot(title, bodyText) {
  return [title ?? '', bodyText ?? ''].join('\n').replace(/\s+/g, ' ').trim();
}

function shouldSuppressFormUpdate(target, snapshot) {
  const targetUrl = String(target?.url ?? '').trim().toLowerCase();
  if (!targetUrl.startsWith('https://forms.gle/')) {
    return false;
  }

  const resolvedUrl = String(snapshot?.resolvedUrl ?? '').trim().toLowerCase();
  if (!resolvedUrl) {
    return false;
  }

  if (!resolvedUrl.includes('docs.google.com/forms/')) {
    return false;
  }

  return true;
}

function makeExcerpt(bodyText, title, resolvedUrl) {
  const pieces = [title, resolvedUrl, bodyText].filter(Boolean);
  const combined = pieces.join(' — ').replace(/\s+/g, ' ').trim();
  return combined.slice(0, 280);
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

    if (parsed.targets && typeof parsed.targets === 'object') {
      return {
        targets: parsed.targets,
      };
    }

    return {
      targets: {},
    };
  } catch {
    return { targets: {} };
  }
}

function saveState(filePath, data) {
  const tempPath = `${filePath}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  fs.renameSync(tempPath, filePath);
}

async function writeAlertFile(content) {
  const candidates = [ALERT_FILE_PATH, FALLBACK_ALERT_FILE_PATH].filter(
    (value, index, array) => value && array.indexOf(value) === index,
  );

  for (const filePath of candidates) {
    try {
      await fs.promises.mkdir(path.dirname(filePath), { recursive: true }).catch(() => {});
      const tempPath = `${filePath}.tmp`;
      await fs.promises.writeFile(tempPath, `${content}\n`, 'utf8');
      await fs.promises.rename(tempPath, filePath);
      if (filePath !== ALERT_FILE_PATH) {
        console.log(`[FORM_PAGE][WARN] alert file fallback used | path=${filePath}`);
      }
      return;
    } catch (error) {
      console.log(
        `[FORM_PAGE][WARN] unable to write alert file | path=${filePath} | ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }
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
          '你监控的页面发生了更新',
          `target=${event.target}`,
          `url=${event.url}`,
          `changedAt=${event.changedAt}`,
        ].join('\n'),
        disable_web_page_preview: 'true',
      }),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[FORM_PAGE][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[FORM_PAGE][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

function loadFormTargets() {
  const jsonTargets = parseTargetsJson(process.env.FORM_PAGE_TARGETS_JSON ?? '');
  if (jsonTargets.length > 0) {
    return jsonTargets;
  }

  const targets = [];
  const primaryUrl = (process.env.FORM_PAGE_TARGET_URL ?? '').trim();
  const primaryName = (process.env.FORM_PAGE_TARGET_NAME ?? 'Google Form 短链').trim();
  if (primaryUrl) {
    targets.push({
      key: `primary::${primaryName}::${primaryUrl}`,
      name: primaryName,
      url: primaryUrl,
    });
  }

  const altUrl = (process.env.FORM_PAGE_TARGET_URL_ALT ?? '').trim();
  if (altUrl && altUrl !== primaryUrl) {
    const altName = (process.env.FORM_PAGE_TARGET_NAME_ALT ?? 'Google Form 最终页').trim();
    targets.push({
      key: `alt::${altName}::${altUrl}`,
      name: altName,
      url: altUrl,
    });
  }

  return targets;
}

function parseTargetsJson(rawValue) {
  if (!rawValue.trim()) {
    return [];
  }

  try {
    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .map((entry, index) => normalizeTargetEntry(entry, index))
      .filter(Boolean);
  } catch {
    return [];
  }
}

function normalizeTargetEntry(entry, index) {
  if (!entry || typeof entry !== 'object') {
    return null;
  }

  const name = String(entry.name ?? entry.label ?? `Google Form ${index + 1}`).trim();
  const url = String(entry.url ?? entry.targetUrl ?? '').trim();
  if (!url) {
    return null;
  }

  return {
    key: String(entry.key ?? `${name}::${url}`),
    name,
    url,
  };
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

function hashContent(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

await main();
