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

const TARGET_NAME = process.env.PUBLIC_PAGE_TARGET_NAME ?? 'Mescladís 公告页';
const TARGET_URL = normalizeTargetUrl(process.env.PUBLIC_PAGE_TARGET_URL ?? '');
const POLL_INTERVAL_MS = readInteger('PUBLIC_PAGE_POLL_INTERVAL_MS', 60_000);
const LANE_INTERVAL_MS = readInteger('MONITOR_LANE_INTERVAL_MS', POLL_INTERVAL_MS);
const LANE_START_OFFSETS_MS = parseLaneOffsets(process.env.MONITOR_LANE_START_OFFSETS_MS);
const PAGE_TIMEOUT_MS = readInteger('PUBLIC_PAGE_PAGE_TIMEOUT_MS', 30_000);
const PAGE_STABILIZE_MS = readInteger('PUBLIC_PAGE_PAGE_STABILIZE_MS', 2_000);
const HEADLESS = (process.env.PUBLIC_PAGE_HEADLESS ?? 'true').toLowerCase() !== 'false';
const ALERT_FILE_PATH = (process.env.PUBLIC_PAGE_ALERT_FILE_PATH ?? '').trim();
const FALLBACK_ALERT_FILE_PATH = path.join(__dirname, 'public_page_alert.txt');
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const STATE_FILE = path.join(__dirname, process.env.PUBLIC_PAGE_STATE_FILE ?? 'public_page_state.json');
const STATE_VERSION = 3;
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
          `[PUBLIC_PAGE] lane start | lane=${laneIndex} | offsetMs=${offsetMs} | target=${TARGET_NAME}`,
        );
      },
      onTick: async ({ laneIndex, cycle }) => {
        const roundStartedAt = new Date().toISOString();
        console.log(
          `[PUBLIC_PAGE] lane #${laneIndex} cycle #${cycle} start | target=${TARGET_NAME} | at=${roundStartedAt}`,
        );

        const snapshot = await probePublicPage();
        if (snapshot.status !== 'ok') {
          console.log(`[PUBLIC_PAGE] probe failed, keeping previous baseline | reason=${snapshot.excerpt}`);
          return;
        }

        const previous = state.current ?? null;
        const currentHash = snapshot.hash;
        const previousHash = previous?.hash ?? null;

        if (!previousHash) {
          state.current = {
            version: STATE_VERSION,
            hash: currentHash,
            title: snapshot.title,
            excerpt: snapshot.excerpt,
            updatedAt: roundStartedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
          console.log(`[PUBLIC_PAGE] baseline seeded | hash=${currentHash}`);
        } else if (previousHash !== currentHash) {
          const changedAt = new Date().toISOString();
          const event = {
            target: TARGET_NAME,
            url: TARGET_URL,
            resolvedUrl: snapshot.resolvedUrl ?? TARGET_URL,
            prevStatus: 'STABLE',
            currStatus: 'UPDATED',
            prevSlots: previous?.excerpt ? [previous.excerpt] : [],
            currSlots: [snapshot.excerpt],
            changedAt,
            reason: 'page_updated',
          };

          const summary = [
            '你监控的页面发生了更新',
            `target=${TARGET_NAME}`,
            `url=${TARGET_URL}`,
            `resolvedUrl=${snapshot.resolvedUrl ?? TARGET_URL}`,
            `changedAt=${changedAt}`,
            `title=${snapshot.title || '-'}`,
            `excerpt=${snapshot.excerpt || '-'}`,
            '',
            JSON.stringify(event),
          ].join('\n');

          console.log(`EVENT_JSON:${JSON.stringify(event)}`);
          void pushToTelegram(event);
          await writeAlertFile(summary);

          state.current = {
            version: STATE_VERSION,
            hash: currentHash,
            title: snapshot.title,
            excerpt: snapshot.excerpt,
            updatedAt: changedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
        } else {
          state.current = {
            version: STATE_VERSION,
            hash: currentHash,
            title: snapshot.title,
            excerpt: snapshot.excerpt,
            updatedAt: previous?.updatedAt ?? roundStartedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
          console.log(`[PUBLIC_PAGE] unchanged | hash=${currentHash}`);
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

async function probePublicPage() {
  if (!TARGET_URL) {
    return {
      hash: hashContent('missing_url'),
      title: '',
      excerpt: 'missing_url',
    };
  }

  try {
    page = page ?? (await browser.newPage());
    page.setDefaultTimeout(PAGE_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: PAGE_TIMEOUT_MS });
    await page.waitForTimeout(PAGE_STABILIZE_MS);

    const snapshot = await page.evaluate(() => {
      const title = (document.title ?? '').trim();
      const candidates = [
        document.querySelector('main'),
        document.querySelector('article'),
        document.querySelector('[role="main"]'),
        document.querySelector('#content'),
        document.querySelector('#primary'),
        document.querySelector('.site-main'),
      ].filter(Boolean);

      const clone = (source) => {
        if (!source) {
          return '';
        }
        const copy = source.cloneNode(true);
        const selectors = [
          '#cmplz-cookiebanner-container',
          '#cmplz-document',
          '.cmplz-cookiebanner',
          '.cmplz-dialog',
          'header',
          'footer',
          'nav',
          'script',
          'style',
          'noscript',
          'svg',
          'iframe',
          '[aria-label*="cookie" i]',
          '[class*="cookie" i]',
        ];
        for (const selector of selectors) {
          copy.querySelectorAll(selector).forEach((node) => node.remove());
        }
        return (copy.innerText ?? '').replace(/\s+/g, ' ').trim();
      };

      let bodyText = '';
      for (const candidate of candidates) {
        bodyText = clone(candidate);
        if (bodyText) {
          break;
        }
      }

      if (!bodyText) {
        bodyText = clone(document.body);
      }

      bodyText = bodyText
        .replace(/Banner Cookies y Panel de Configuración[\s\S]*?Rechazo todas las cookies/gi, ' ')
        .replace(/Open Mobile Nav/gi, ' ')
        .replace(/Facebook Instagram Youtube Twitter\/X/gi, ' ')
        .replace(/\s+/g, ' ')
        .trim();

      return { title, bodyText };
    });

    const normalized = normalizeSnapshot(snapshot.title, snapshot.bodyText);
    const resolvedUrl = normalizeTargetUrl(page.url());
    return {
      status: 'ok',
      hash: hashContent(normalized),
      title: snapshot.title,
      excerpt: makeExcerpt(snapshot.bodyText, snapshot.title),
      resolvedUrl,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`[PUBLIC_PAGE][ERROR] ${message}`);
    return {
      status: 'error',
      hash: hashContent(`error:${message}`),
      title: '',
      excerpt: message,
      resolvedUrl: TARGET_URL,
    };
  }
}

function normalizeSnapshot(title, bodyText) {
  return [title ?? '', bodyText ?? ''].join('\n').replace(/\s+/g, ' ').trim();
}

function makeExcerpt(bodyText, title) {
  const pieces = [title, bodyText].filter(Boolean);
  const combined = pieces.join(' — ').replace(/\s+/g, ' ').trim();
  return combined.slice(0, 280);
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

async function writeAlertFile(content) {
  const candidates = [ALERT_FILE_PATH, FALLBACK_ALERT_FILE_PATH].filter(
    (value, index, array) => value && array.indexOf(value) === index,
  );

  for (const filePath of candidates) {
    try {
      await fs.promises.mkdir(path.dirname(filePath), { recursive: true }).catch(() => {});
      await fs.promises.writeFile(filePath, `${content}\n`, 'utf8');
      if (filePath !== ALERT_FILE_PATH) {
        console.log(`[PUBLIC_PAGE][WARN] alert file fallback used | path=${filePath}`);
      }
      return;
    } catch (error) {
      console.log(
        `[PUBLIC_PAGE][WARN] unable to write alert file | path=${filePath} | ${
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
        `[PUBLIC_PAGE][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[PUBLIC_PAGE][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
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
