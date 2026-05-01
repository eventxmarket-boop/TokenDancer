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

const TARGET_NAME = process.env.MESCLADIS_HOME_BUTTON_TARGET_NAME ?? 'Mescladís Nuevas citas';
const TARGET_URL = normalizeTargetUrl(process.env.MESCLADIS_HOME_BUTTON_TARGET_URL ?? 'https://mescladis.org/');
const BUTTON_TEXT = process.env.MESCLADIS_HOME_BUTTON_TEXT ?? 'Nuevas citas';
const BUTTON_TEXT_NORM = normalizeText(BUTTON_TEXT);
const POLL_INTERVAL_MS = readInteger('MESCLADIS_HOME_BUTTON_POLL_INTERVAL_MS', 60_000);
const LANE_INTERVAL_MS = readInteger('MESCLADIS_HOME_BUTTON_LANE_INTERVAL_MS', POLL_INTERVAL_MS);
const LANE_START_OFFSETS_MS = parseLaneOffsets(
  process.env.MESCLADIS_HOME_BUTTON_LANE_START_OFFSETS_MS ?? '0',
);
const PAGE_TIMEOUT_MS = readInteger('MESCLADIS_HOME_BUTTON_PAGE_TIMEOUT_MS', 30_000);
const PAGE_STABILIZE_MS = readInteger('MESCLADIS_HOME_BUTTON_PAGE_STABILIZE_MS', 2_000);
const HEADLESS = (process.env.MESCLADIS_HOME_BUTTON_HEADLESS ?? 'true').toLowerCase() !== 'false';
const ALERT_FILE_PATH = (process.env.MESCLADIS_HOME_BUTTON_ALERT_FILE_PATH ?? '').trim();
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const STATE_FILE = path.join(
  __dirname,
  process.env.MESCLADIS_HOME_BUTTON_STATE_FILE ?? 'mescladis_home_button_state.json',
);
const STATE_VERSION = 1;
const monitorStartedAt = new Date().toISOString();

const stopSignals = new Set();
let browser = null;
let page = null;

process.on('SIGINT', () => {
  stopSignals.add('SIGINT');
});

process.on('SIGTERM', () => {
  stopSignals.add('SIGTERM');
});

async function main() {
  browser = await chromium.launch({ headless: HEADLESS });

  try {
    const state = loadState();

    await runSerializedLaneScheduler({
      laneStartOffsetsMs: LANE_START_OFFSETS_MS,
      laneIntervalMs: LANE_INTERVAL_MS,
      stopSignals,
      onLaneStart: ({ laneIndex, offsetMs }) => {
        console.log(
          `[HOME_BUTTON] lane start | lane=${laneIndex} | offsetMs=${offsetMs} | target=${TARGET_NAME}`,
        );
      },
      onTick: async ({ laneIndex, cycle }) => {
        const roundStartedAt = new Date().toISOString();
        console.log(
          `[HOME_BUTTON] lane #${laneIndex} cycle #${cycle} start | target=${TARGET_NAME} | at=${roundStartedAt}`,
        );

        const snapshot = await probeHomeButton();
        const previous = state.current ?? null;
        const currentHash = snapshot.hash;
        const previousHash = previous?.hash ?? null;

        if (!previousHash) {
          state.current = {
            version: STATE_VERSION,
            hash: currentHash,
            title: snapshot.title,
            buttonSummary: snapshot.buttonSummary,
            updatedAt: roundStartedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
          console.log(`[HOME_BUTTON] baseline seeded | hash=${currentHash}`);
        } else if (previousHash !== currentHash) {
          const changedAt = new Date().toISOString();
          const event = {
            target: TARGET_NAME,
            url: TARGET_URL,
            resolvedUrl: snapshot.resolvedUrl ?? TARGET_URL,
            prevStatus: 'STABLE',
            currStatus: 'UPDATED',
            prevSlots: previous?.buttonSummary ? [previous.buttonSummary] : [],
            currSlots: [snapshot.buttonSummary],
            changedAt,
            reason: 'button_changed',
          };

          const summary = [
            '你监控的页面发生了更新',
            `target=${TARGET_NAME}`,
            `url=${TARGET_URL}`,
            `resolvedUrl=${snapshot.resolvedUrl ?? TARGET_URL}`,
            `changedAt=${changedAt}`,
            `title=${snapshot.title || '-'}`,
            `button=${snapshot.buttonSummary || '-'}`,
            '',
            JSON.stringify(event),
          ].join('\n');

          console.log(`EVENT_JSON:${JSON.stringify(event)}`);
          void pushToTelegram(event);
          if (ALERT_FILE_PATH) {
            await writeAlertFile(ALERT_FILE_PATH, summary);
          }

          state.current = {
            version: STATE_VERSION,
            hash: currentHash,
            title: snapshot.title,
            buttonSummary: snapshot.buttonSummary,
            updatedAt: changedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
        } else {
          state.current = {
            version: STATE_VERSION,
            hash: currentHash,
            title: snapshot.title,
            buttonSummary: snapshot.buttonSummary,
            updatedAt: previous?.updatedAt ?? roundStartedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
          console.log(`[HOME_BUTTON] unchanged | hash=${currentHash}`);
        }
      },
    });
  } finally {
    if (page) {
      await page.close().catch(() => {});
    }
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function probeHomeButton() {
  if (!TARGET_URL) {
    return {
      hash: hashContent('missing_url'),
      title: '',
      buttonSummary: 'missing_url',
      resolvedUrl: '',
    };
  }

  try {
    page = page ?? (await browser.newPage());
    page.setDefaultTimeout(PAGE_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: PAGE_TIMEOUT_MS });
    await page.waitForTimeout(PAGE_STABILIZE_MS);

    const snapshot = await page.evaluate((buttonTextNorm) => {
      const title = (document.title ?? '').trim();
      const normalize = (value) =>
        (value ?? '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .replace(/\s+/g, ' ')
          .trim()
          .toLowerCase();

      const isVisible = (element) => {
        if (!element) {
          return false;
        }

        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return (
          style &&
          style.display !== 'none' &&
          style.visibility !== 'hidden' &&
          rect.width > 0 &&
          rect.height > 0
        );
      };

      const candidates = Array.from(
        document.querySelectorAll('a, button, [role="button"], input[type="button"], input[type="submit"]'),
      );

      const matches = candidates
        .filter((element) => isVisible(element))
        .map((element) => {
          const text = (element.innerText || element.textContent || '').replace(/\s+/g, ' ').trim();
          const href =
            element instanceof HTMLAnchorElement
              ? element.href
              : element.getAttribute('href') || element.getAttribute('data-href') || '';
          const aria = element.getAttribute('aria-label') || '';
          const titleAttr = element.getAttribute('title') || '';
          const role = element.getAttribute('role') || '';
          return {
            tag: element.tagName.toLowerCase(),
            text,
            href,
            aria,
            title: titleAttr,
            role,
          };
        })
        .filter((entry) => {
          const haystack = [entry.text, entry.href, entry.aria, entry.title, entry.role]
            .map(normalize)
            .join(' | ');
          return haystack.includes(buttonTextNorm);
        })
        .slice(0, 12);

      return { title, matches };
    }, BUTTON_TEXT_NORM);

    const resolvedUrl = normalizeTargetUrl(page.url());
    const buttonSummary = formatButtonSummary(snapshot.matches);
    return {
      hash: hashContent(JSON.stringify({ title: snapshot.title, resolvedUrl, matches: snapshot.matches })),
      title: snapshot.title,
      buttonSummary,
      resolvedUrl,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`[HOME_BUTTON][ERROR] ${message}`);
    return {
      hash: hashContent(`error:${message}`),
      title: '',
      buttonSummary: message,
      resolvedUrl: TARGET_URL,
    };
  }
}

function formatButtonSummary(matches) {
  if (!Array.isArray(matches) || matches.length === 0) {
    return 'button_missing';
  }

  return matches
    .map((entry) => {
      const parts = [entry.text || '-', entry.href || '-'];
      return parts.join(' -> ');
    })
    .join(' | ')
    .slice(0, 280);
}

function normalizeSnapshot(title, bodyText) {
  return [title ?? '', bodyText ?? ''].join('\n').replace(/\s+/g, ' ').trim();
}

function normalizeTargetUrl(value) {
  const trimmed = (value ?? '').trim();
  if (!trimmed) {
    return '';
  }

  try {
    const url = new URL(trimmed);
    url.search = '';
    url.hash = '';
    return url.toString();
  } catch {
    return trimmed.split('?')[0].split('#')[0];
  }
}

function normalizeText(value) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function loadState() {
  try {
    if (!fs.existsSync(STATE_FILE)) {
      return { current: null };
    }

    const parsed = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    if (!parsed || typeof parsed !== 'object') {
      return { current: null };
    }

    return {
      current:
        parsed.current &&
        typeof parsed.current === 'object' &&
        Number(parsed.current.version) === STATE_VERSION
          ? parsed.current
          : null,
    };
  } catch {
    return { current: null };
  }
}

function saveState(filePath, data) {
  const tempPath = `${filePath}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  fs.renameSync(tempPath, filePath);
}

async function writeAlertFile(filePath, content) {
  await fs.promises.mkdir(path.dirname(filePath), { recursive: true }).catch(() => {});
  await fs.promises.writeFile(filePath, `${content}\n`, 'utf8');
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
        `[HOME_BUTTON][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[HOME_BUTTON][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
    );
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

function hashContent(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

await main();
