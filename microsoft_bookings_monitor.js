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

const TARGET_NAME = process.env.MICROSOFT_BOOKINGS_TARGET_NAME ?? 'Microsoft Bookings 监控页';
const TARGET_URL = (process.env.MICROSOFT_BOOKINGS_TARGET_URL ?? '').trim();
const POLL_INTERVAL_MS = readInteger('MICROSOFT_BOOKINGS_POLL_INTERVAL_MS', 60_000);
const LANE_INTERVAL_MS = readInteger('MONITOR_LANE_INTERVAL_MS', POLL_INTERVAL_MS);
const LANE_START_OFFSETS_MS = parseLaneOffsets(process.env.MONITOR_LANE_START_OFFSETS_MS);
const STABILITY_ROUNDS = readInteger('MICROSOFT_BOOKINGS_STABILITY_ROUNDS', 2);
const PAGE_TIMEOUT_MS = readInteger('MICROSOFT_BOOKINGS_PAGE_TIMEOUT_MS', 30_000);
const PAGE_STABILIZE_MS = readInteger('MICROSOFT_BOOKINGS_PAGE_STABILIZE_MS', 2_000);
const MONTH_SCAN_COUNT = readInteger('MICROSOFT_BOOKINGS_MONTH_SCAN_COUNT', 3);
const HEADLESS = (process.env.MICROSOFT_BOOKINGS_HEADLESS ?? 'true').toLowerCase() !== 'false';
const ALERT_FILE_PATH = (process.env.MICROSOFT_BOOKINGS_ALERT_FILE_PATH ?? '').trim();
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const STATE_FILE = path.join(
  __dirname,
  process.env.MICROSOFT_BOOKINGS_STATE_FILE ?? 'microsoft_bookings_state.json',
);
const monitorStartedAt = new Date().toISOString();

if (!TARGET_URL) {
  throw new Error('MICROSOFT_BOOKINGS_TARGET_URL is required');
}

const stopSignals = new Set();
let browser = null;

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
          `[MS_BOOKINGS] lane start | lane=${laneIndex} | offsetMs=${offsetMs} | target=${TARGET_NAME}`,
        );
      },
      onTick: async ({ laneIndex, cycle }) => {
        const roundStartedAt = new Date().toISOString();
        console.log(
          `[MS_BOOKINGS] lane #${laneIndex} cycle #${cycle} start | target=${TARGET_NAME} | at=${roundStartedAt}`,
        );

        const snapshot = await probeMicrosoftBookings();
        const previous = state.current ?? null;
        const pending = state.pending ?? null;
        const currentHash = snapshot.hash;
        const previousHash = previous?.hash ?? null;
        const pendingMatchesCurrent = pending?.hash === currentHash && Array.isArray(pending.dates);
        const stableMatchesCurrent = !previousHash || areSameDateLists(previous?.dates ?? [], snapshot.dates);

        if (!previousHash) {
          state.current = {
            hash: currentHash,
            title: snapshot.title,
            excerpt: snapshot.excerpt,
            resolvedUrl: snapshot.resolvedUrl,
            earliestDate: snapshot.earliestDate,
            dateCount: snapshot.dateCount,
            dates: snapshot.dates,
            updatedAt: roundStartedAt,
            monitorStartedAt,
          };
          state.pending = null;
          saveState(STATE_FILE, state);
          console.log(`[MS_BOOKINGS] baseline seeded | hash=${currentHash}`);
          if (STABILITY_ROUNDS <= 1) {
            state.pending = null;
          }
          saveState(STATE_FILE, state);
        } else if (stableMatchesCurrent) {
          state.pending = null;
          state.current = {
            hash: currentHash,
            title: snapshot.title,
            excerpt: snapshot.excerpt,
            resolvedUrl: snapshot.resolvedUrl,
            earliestDate: snapshot.earliestDate,
            dateCount: snapshot.dateCount,
            dates: snapshot.dates,
            updatedAt: previous?.updatedAt ?? roundStartedAt,
            monitorStartedAt,
          };
          saveState(STATE_FILE, state);
          console.log(
            `[MS_BOOKINGS] unchanged | hash=${currentHash} | earliestDate=${snapshot.earliestDate || '-'} | dateCount=${snapshot.dateCount}`,
          );
        } else {
          const nextPending = pendingMatchesCurrent
            ? {
                ...pending,
                seenCount: (pending.seenCount ?? 1) + 1,
                updatedAt: roundStartedAt,
              }
            : {
                hash: currentHash,
                title: snapshot.title,
                excerpt: snapshot.excerpt,
                resolvedUrl: snapshot.resolvedUrl,
                earliestDate: snapshot.earliestDate,
                dateCount: snapshot.dateCount,
                dates: snapshot.dates,
                updatedAt: roundStartedAt,
                monitorStartedAt,
                seenCount: 1,
              };

          state.pending = nextPending;
          saveState(STATE_FILE, state);
          console.log(
            `[MS_BOOKINGS] pending | hash=${currentHash} | seen=${nextPending.seenCount}/${STABILITY_ROUNDS} | earliestDate=${snapshot.earliestDate || '-'} | dateCount=${snapshot.dateCount}`,
          );

          if (nextPending.seenCount >= STABILITY_ROUNDS) {
            const changedAt = new Date().toISOString();
            const reason = getDateChangeReason(previous?.dates ?? [], snapshot.dates);

            const event = {
              target: TARGET_NAME,
              url: TARGET_URL,
              resolvedUrl: snapshot.resolvedUrl,
              prevStatus: 'STABLE',
              currStatus: 'UPDATED',
              prevSlots: previous?.dates?.length ? previous.dates : [],
              currSlots: snapshot.dates,
              changedAt,
              reason,
              earliestDate: snapshot.earliestDate,
              dateCount: snapshot.dateCount,
            };

            const summary = [
              '你监控的页面发生了更新',
              `target=${TARGET_NAME}`,
              `url=${TARGET_URL}`,
              `resolvedUrl=${snapshot.resolvedUrl || '-'}`,
              `changedAt=${changedAt}`,
              `earliestDate=${snapshot.earliestDate || '-'}`,
              `dateCount=${snapshot.dateCount}`,
              `title=${snapshot.title || '-'}`,
              `excerpt=${snapshot.excerpt || '-'}`,
              '',
              JSON.stringify(event),
            ].join('\n');

            console.log(`EVENT_JSON:${JSON.stringify(event)}`);
            void pushToTelegram(event);
            if (ALERT_FILE_PATH) {
              await writeAlertFile(ALERT_FILE_PATH, summary);
            }

            state.current = {
              hash: currentHash,
              title: snapshot.title,
              excerpt: snapshot.excerpt,
              resolvedUrl: snapshot.resolvedUrl,
              earliestDate: snapshot.earliestDate,
              dateCount: snapshot.dateCount,
              dates: snapshot.dates,
              updatedAt: changedAt,
              monitorStartedAt,
            };
            state.pending = null;
            saveState(STATE_FILE, state);
          }
        }
      },
    });
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function probeMicrosoftBookings() {
  const page = await browser.newPage();

  try {
    page.setDefaultTimeout(PAGE_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: PAGE_TIMEOUT_MS });
    await page.waitForTimeout(PAGE_STABILIZE_MS);

    const availableDates = [];
    const baseMonthContext = getMonthContext(new Date());
    for (let monthIndex = 0; monthIndex < MONTH_SCAN_COUNT; monthIndex += 1) {
      const snapshot = await captureSnapshot(page);
      const monthContext = shiftMonthContext(baseMonthContext, monthIndex);
      const controls = await collectDateControls(page, monthContext);
      let foundDate = '';

      for (const control of controls) {
        const probeResult = await probeDateControl(page, control);
        if (probeResult.available) {
          foundDate = control.isoDate;
          availableDates.push(control.isoDate);
          break;
        }
      }

      if (monthIndex < MONTH_SCAN_COUNT - 1) {
        const moved = await goToNextMonth(page);
        if (!moved) {
          break;
        }
        await page.waitForTimeout(PAGE_STABILIZE_MS);
      }
    }

    const dates = [...new Set(availableDates)].sort();
    const earliestDate = dates[0] ?? '';
    const lastSnapshot = await captureSnapshot(page);
    const resolvedUrl = lastSnapshot.resolvedUrl ?? page.url().trim();
    const title = lastSnapshot.title;
    const bodyText = lastSnapshot.bodyText;
    const excerpt = makeExcerpt(title, resolvedUrl, bodyText, dates);

    return {
      hash: hashContent([resolvedUrl, dates.join(',')].join('\n')),
      title,
      resolvedUrl,
      bodyText,
      frameTexts: lastSnapshot.frameTexts,
      excerpt,
      dates,
      dateCount: dates.length,
      earliestDate,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`[MS_BOOKINGS][ERROR] ${message}`);
    return {
      hash: hashContent(`error:${message}`),
      title: '',
      resolvedUrl: '',
      bodyText: '',
      frameTexts: [],
      excerpt: message,
      dates: [],
      dateCount: 0,
      earliestDate: '',
    };
  } finally {
    await page.close().catch(() => {});
  }
}

async function collectDateControls(page, monthContext) {
  const controls = [];
  const frames = getFrames(page);

  for (const [frameIndex, frame] of frames.entries()) {
    try {
      const items = await frame.locator('button, [role="button"], a').evaluateAll((elements) =>
        elements.map((element, index) => {
          const text = (element.innerText ?? element.textContent ?? '').replace(/\s+/g, ' ').trim();
          const ariaLabel = (element.getAttribute('aria-label') ?? '').replace(/\s+/g, ' ').trim();
          const title = (element.getAttribute('title') ?? '').replace(/\s+/g, ' ').trim();
          const disabled =
            element.hasAttribute('disabled') || element.getAttribute('aria-disabled') === 'true';
          const rect = element.getBoundingClientRect();
          const style = window.getComputedStyle(element);
          const visible =
            rect.width > 0 &&
            rect.height > 0 &&
            style.display !== 'none' &&
            style.visibility !== 'hidden';

          return { index, text, ariaLabel, title, disabled, visible };
        }),
      );

      for (const item of items) {
        if (!item.visible || item.disabled) {
          continue;
        }

        const label = normalizeCandidateLabel(item.text, item.ariaLabel, item.title);
        if (!looksLikeDateControl(label)) {
          continue;
        }

        const isoDate = resolveCandidateDate(label, monthContext);
        if (!isoDate) {
          continue;
        }

        controls.push({
          frameIndex,
          index: item.index,
          label,
          isoDate,
        });
      }
    } catch {
      // Ignore transient frames or inaccessible views.
    }
  }

  return dedupeControls(
    controls.sort((left, right) => left.isoDate.localeCompare(right.isoDate)),
  );
}

async function probeDateControl(page, control) {
  const frames = getFrames(page);
  const frame = frames[control.frameIndex];
  if (!frame) {
    return { available: false, reason: 'frame_missing' };
  }

  const locator = frame.locator('button, [role="button"], a').nth(control.index);
  try {
    if (!(await locator.count())) {
      return { available: false, reason: 'missing' };
    }
    if (!(await locator.isVisible().catch(() => false))) {
      return { available: false, reason: 'hidden' };
    }

    const before = await captureSnapshot(page);
    await locator.click({ timeout: PAGE_TIMEOUT_MS, noWaitAfter: true });
    await waitForSnapshotShift(page, before);

    const after = await captureSnapshot(page);
    const normalized = normalizeSnapshot(after.resolvedUrl, after.title, after.bodyText, after.frameTexts);

    if (hasNoAvailabilityText(normalized)) {
      return { available: false, reason: 'no_availability_text' };
    }

    const times = extractTimes(normalized);
    if (times.length > 0) {
      return { available: true, times, reason: 'times_visible' };
    }

    return { available: false, reason: 'no_times' };
  } catch {
    return { available: false, reason: 'click_failed' };
  }
}

async function goToNextMonth(page) {
  const selectors = [
    'button[aria-label*="Next" i]',
    'button[aria-label*="Siguiente" i]',
    'button[title*="Next" i]',
    'button[title*="Siguiente" i]',
    'button:has-text("Next")',
    'button:has-text("Siguiente")',
    '[role="button"][aria-label*="Next" i]',
    '[role="button"][aria-label*="Siguiente" i]',
  ];

  const frames = [page.mainFrame(), ...page.frames().filter((frame) => frame !== page.mainFrame())];
  for (const frame of frames) {
    for (const selector of selectors) {
      let locator = null;
      try {
        locator = frame.locator(selector).first();
      } catch {
        continue;
      }

      try {
        if (!(await locator.count())) {
          continue;
        }
        if (!(await locator.isVisible().catch(() => false))) {
          continue;
        }

        const before = await captureSnapshot(page);
        await locator.click({ timeout: PAGE_TIMEOUT_MS, noWaitAfter: true });
        await waitForSnapshotShift(page, before);
        return true;
      } catch {
        // Try the next candidate.
      }
    }
  }

  return false;
}

async function waitForSnapshotShift(page, beforeSnapshot) {
  const deadline = Date.now() + PAGE_TIMEOUT_MS;
  const beforeFingerprint = hashContent(
    normalizeSnapshot(
      beforeSnapshot.resolvedUrl,
      beforeSnapshot.title,
      beforeSnapshot.bodyText,
      beforeSnapshot.frameTexts,
    ),
  );

  while (Date.now() < deadline) {
    await page.waitForTimeout(500);
    const current = await captureSnapshot(page);
    const currentFingerprint = hashContent(
      normalizeSnapshot(current.resolvedUrl, current.title, current.bodyText, current.frameTexts),
    );

    if (currentFingerprint !== beforeFingerprint) {
      return;
    }
  }
}

function getFrames(page) {
  return [page.mainFrame(), ...page.frames().filter((frame) => frame !== page.mainFrame())];
}

async function captureSnapshot(page) {
  const topSnapshot = await page.evaluate(() => {
    const title = (document.title ?? '').trim();
    const bodyText = (document.body?.innerText ?? '').replace(/\s+/g, ' ').trim();
    return { title, bodyText };
  });

  const frameTexts = [];
  for (const frame of page.frames()) {
    if (frame === page.mainFrame()) {
      continue;
    }

    try {
      const frameSnapshot = await frame.evaluate(() => {
        const title = (document.title ?? '').trim();
        const bodyText = (document.body?.innerText ?? '').replace(/\s+/g, ' ').trim();
        return { title, bodyText };
      });
      const frameLabel = [frame.url(), frameSnapshot.title].filter(Boolean).join(' | ');
      if (frameSnapshot.bodyText || frameLabel) {
        frameTexts.push([frameLabel, frameSnapshot.bodyText].filter(Boolean).join(' — '));
      }
    } catch {
      // Some frames may be transient or inaccessible; ignore and keep probing.
    }
  }

  return {
    title: topSnapshot.title,
    bodyText: topSnapshot.bodyText,
    frameTexts,
    resolvedUrl: page.url().trim(),
  };
}

function normalizeSnapshot(resolvedUrl, title, bodyText, frameTexts) {
  return [resolvedUrl ?? '', title ?? '', bodyText ?? '', ...(frameTexts ?? [])]
    .join('\n')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeCandidateLabel(text, ariaLabel, title) {
  return [text, ariaLabel, title].filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
}

function looksLikeDateControl(label) {
  const normalized = (label ?? '').replace(/\s+/g, ' ').trim();
  if (!normalized) {
    return false;
  }

  const lower = normalized.toLowerCase();
  if (
    lower.includes('next') ||
    lower.includes('siguiente') ||
    lower.includes('previous') ||
    lower.includes('anterior') ||
    lower.includes('back') ||
    lower.includes('forward') ||
    lower.includes('today') ||
    lower.includes('hoy') ||
    lower.includes('bookings') ||
    lower.includes('outlook')
  ) {
    return false;
  }

  if (/\d{1,2}:\d{2}/.test(normalized)) {
    return false;
  }

  if (extractDates(normalized).length > 0) {
    return true;
  }

  return /^\d{1,2}$/.test(normalized);
}

function resolveCandidateDate(label, monthContext) {
  const normalized = (label ?? '').replace(/\s+/g, ' ').trim();
  if (!normalized) {
    return null;
  }

  const explicitDates = extractDates(normalized);
  if (explicitDates.length > 0) {
    return explicitDates[0];
  }

  if (!monthContext || !Number.isInteger(monthContext.year) || !Number.isInteger(monthContext.month)) {
    return null;
  }

  if (!/^\d{1,2}$/.test(normalized)) {
    return null;
  }

  return formatIsoDate(monthContext.year, monthContext.month, Number(normalized));
}

function getMonthContext(referenceDate = new Date()) {
  return {
    year: referenceDate.getFullYear(),
    month: referenceDate.getMonth() + 1,
  };
}

function shiftMonthContext(baseContext, offsetMonths) {
  const monthIndex = baseContext.month - 1 + offsetMonths;
  const year = baseContext.year + Math.floor(monthIndex / 12);
  const month = ((monthIndex % 12) + 12) % 12 + 1;
  return { year, month };
}

function extractTimes(text) {
  const normalized = (text ?? '').replace(/\s+/g, ' ').trim();
  const matches = new Set();

  for (const match of normalized.matchAll(/\b([01]?\d|2[0-3]):([0-5]\d)(?:\s?(?:AM|PM|am|pm))?\b/g)) {
    matches.add(`${match[1]}:${match[2]}`);
  }

  return [...matches].sort();
}

function hasNoAvailabilityText(text) {
  const normalized = (text ?? '').replace(/\s+/g, ' ').trim().toLowerCase();
  return (
    normalized.includes('no hay disponibilidad en esta fecha') ||
    normalized.includes('elija otra') ||
    normalized.includes('no availability on this date') ||
    normalized.includes('choose another') ||
    normalized.includes('no hay horas disponibles')
  );
}

function dedupeControls(controls) {
  const seen = new Set();
  const result = [];
  for (const control of controls) {
    const key = `${control.frameIndex}:${control.index}:${control.isoDate}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(control);
  }
  return result;
}

function makeExcerpt(title, resolvedUrl, bodyText, dates) {
  const pieces = [title, resolvedUrl, bodyText].filter(Boolean);
  if (dates.length > 0) {
    pieces.unshift(`dates=${dates.slice(0, 12).join(', ')}`);
  }
  const combined = pieces.join(' — ').replace(/\s+/g, ' ').trim();
  return combined.slice(0, 320);
}

function areSameDateLists(previousDates, currentDates) {
  if (!Array.isArray(previousDates) || !Array.isArray(currentDates)) {
    return false;
  }

  if (previousDates.length !== currentDates.length) {
    return false;
  }

  for (let index = 0; index < previousDates.length; index += 1) {
    if (previousDates[index] !== currentDates[index]) {
      return false;
    }
  }

  return true;
}

function getDateChangeReason(previousDates, currentDates) {
  if (currentDates.length > previousDates.length) {
    return 'date_count_increased';
  }

  if (currentDates.length < previousDates.length) {
    return 'date_count_decreased';
  }

  const previousSet = new Set(previousDates);
  const currentSet = new Set(currentDates);
  for (const date of currentSet) {
    if (!previousSet.has(date)) {
      return 'date_set_changed';
    }
  }

  for (const date of previousSet) {
    if (!currentSet.has(date)) {
      return 'date_set_changed';
    }
  }

  return 'date_set_changed';
}

function formatIsoDate(year, month, day) {
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) {
    return null;
  }
  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return null;
  }

  const iso = `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  const test = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(test.getTime())) {
    return null;
  }

  return iso;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function loadState() {
  try {
    if (!fs.existsSync(STATE_FILE)) {
      return { current: null, pending: null };
    }

    const parsed = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    if (!parsed || typeof parsed !== 'object') {
      return { current: null, pending: null };
    }

    return {
      current: parsed.current && typeof parsed.current === 'object' ? parsed.current : null,
      pending: parsed.pending && typeof parsed.pending === 'object' ? parsed.pending : null,
    };
  } catch {
    return { current: null, pending: null };
  }
}

function saveState(filePath, data) {
  const tempPath = `${filePath}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  fs.renameSync(tempPath, filePath);
}

async function writeAlertFile(filePath, content) {
  await fs.promises.mkdir(path.dirname(filePath), { recursive: true }).catch(() => {});
  const tempPath = `${filePath}.tmp`;
  await fs.promises.writeFile(tempPath, `${content}\n`, 'utf8');
  await fs.promises.rename(tempPath, filePath);
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
          'Microsoft Bookings 页面发生更新',
          `target=${event.target}`,
          `url=${event.url}`,
          `resolvedUrl=${event.resolvedUrl || '-'}`,
          `earliestDate=${event.earliestDate || '-'}`,
          `dateCount=${event.dateCount ?? 0}`,
          `changedAt=${event.changedAt}`,
        ].join('\n'),
        disable_web_page_preview: 'true',
      }),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[MS_BOOKINGS][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[MS_BOOKINGS][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
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
