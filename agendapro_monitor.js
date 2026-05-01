#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { parseLaneOffsets, runSerializedLaneScheduler } from './monitor_lane_scheduler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvFile(path.join(__dirname, '.env'));

const targets = [
  { name: process.env.AGENDAPRO_TARGET_1_NAME ?? 'Fundación Ibn', url: process.env.AGENDAPRO_TARGET_1_URL ?? '' },
  { name: process.env.AGENDAPRO_TARGET_2_NAME ?? 'Agendapro 2', url: process.env.AGENDAPRO_TARGET_2_URL ?? '' },
  { name: process.env.AGENDAPRO_TARGET_3_NAME ?? 'Agendapro 3', url: process.env.AGENDAPRO_TARGET_3_URL ?? '' },
].filter((target) => target.url);

const POLL_INTERVAL_MS = readInteger('AGENDAPRO_POLL_INTERVAL_MS', 60_000);
const LANE_INTERVAL_MS = readInteger('MONITOR_LANE_INTERVAL_MS', POLL_INTERVAL_MS);
const LANE_START_OFFSETS_MS = parseLaneOffsets(process.env.MONITOR_LANE_START_OFFSETS_MS);
const PAGE_TIMEOUT_MS = readInteger('AGENDAPRO_PAGE_TIMEOUT_MS', 45_000);
const HEADLESS = (process.env.AGENDAPRO_HEADLESS ?? 'true').toLowerCase() !== 'false';
const MONITOR_TIMEZONE = process.env.AGENDAPRO_TIMEZONE ?? process.env.MONITOR_TIMEZONE ?? 'Europe/Madrid';
const ALERT_FILE_PATH = (process.env.AGENDAPRO_ALERT_FILE_PATH ?? '').trim();
const TELEGRAM_BOT_TOKEN = (process.env.TELEGRAM_BOT_TOKEN ?? '').trim();
const TELEGRAM_CHAT_ID = (process.env.TELEGRAM_CHAT_ID ?? '').trim();
const STATE_FILE = path.join(__dirname, process.env.AGENDAPRO_STATE_FILE ?? 'agendapro_state.json');

const stopSignals = new Set();
let browser = null;
const targetPages = new Map();

process.on('SIGINT', () => stopSignals.add('SIGINT'));
process.on('SIGTERM', () => stopSignals.add('SIGTERM'));

async function main() {
  validateTargets(targets);
  const snapshots = new Map(Object.entries(loadState().targets ?? {}));

  browser = await chromium.launch({ headless: HEADLESS });

  try {
    await runSerializedLaneScheduler({
      laneStartOffsetsMs: LANE_START_OFFSETS_MS,
      laneIntervalMs: LANE_INTERVAL_MS,
      stopSignals,
      onLaneStart: ({ laneIndex, offsetMs }) => {
        console.log(
          `[AGENDAPRO] lane start | lane=${laneIndex} | offsetMs=${offsetMs} | targets=${targets.length}`,
        );
      },
      onTick: async ({ laneIndex, cycle }) => {
        console.log(
          `[AGENDAPRO] lane #${laneIndex} cycle #${cycle} start at ${new Date().toISOString()}`,
        );
        await runRound({ roundId: `${laneIndex}.${cycle}`, snapshots });
      },
    });
  } finally {
    for (const page of targetPages.values()) {
      await page.close().catch(() => {});
    }
    targetPages.clear();

    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function runRound({ roundId, snapshots }) {
  for (const target of targets) {
    if (stopSignals.size) {
      break;
    }

    const curr = await probeTarget(target);
    const targetRecord = getTargetRecord(snapshots, target.name);
    const prev = getTargetSnapshot(targetRecord);
    const changedAt = new Date().toISOString();
    const event = buildEvent(target, prev, curr, changedAt);

    console.log(
      `[AGENDAPRO] #${roundId} ${target.name} | ${curr.status}` +
        (curr.status === 'OPEN' ? ` | dates=${curr.dates.join(', ') || '-'}` : '') +
        (curr.status === 'ERROR' ? ` | error=${curr.reason ?? 'unknown'}` : ''),
    );

    if (event) {
      console.log(`EVENT_JSON:${JSON.stringify(event)}`);
      void pushToTelegram(event);
      if (ALERT_FILE_PATH) {
        void writeAlertFile(event);
      }
    }

    setTargetSnapshot(targetRecord, {
      status: curr.status,
      dates: curr.dates,
      times: curr.times,
      updatedAt: changedAt,
      roundId,
    });
  }

  saveState(STATE_FILE, { targets: Object.fromEntries(snapshots.entries()) });
}

async function probeTarget(target) {
  if (!target.url) {
    return { status: 'ERROR', dates: [], times: [], reason: 'missing_url' };
  }

  try {
    const page = await getTargetPage(target.name);
    page.setDefaultTimeout(PAGE_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(PAGE_TIMEOUT_MS);

    await page.goto(target.url, { waitUntil: 'domcontentloaded', timeout: PAGE_TIMEOUT_MS });
    await page.waitForTimeout(2_000);
    await page
      .waitForFunction(
        () => {
          const text = (document.body?.innerText ?? '').replace(/\s+/g, ' ').trim().toLowerCase();
          return (
            text.includes('agendar ahora') ||
            text.includes('ver todas las fechas disponibles') ||
            text.includes('no hay horas disponibles para esta selección') ||
            text.includes('selecciona fecha y hora de tu servicio')
          );
        },
        { timeout: 6_000 },
      )
      .catch(() => {});

    const bookingRoot = await resolveBookingRoot(page);
    let opened = false;
    if (bookingRoot) {
      console.log(`[AGENDAPRO][FLOW] ${target.name} | click Agendar servicio`);
      const clickedService = await clickAgendarServicio(bookingRoot);
      console.log(`[AGENDAPRO][FLOW] ${target.name} | Agendar servicio clicked=${clickedService}`);
      if (!clickedService) {
        console.log(`[AGENDAPRO][FLOW] ${target.name} | click Ver horario fallback`);
        const clickedHorario = await clickVerHorario(bookingRoot);
        console.log(`[AGENDAPRO][FLOW] ${target.name} | Ver horario clicked=${clickedHorario}`);
      }
      await settleAfterAction(bookingRoot, 1_000);

      const postEntryRoot = (await resolveBookingRoot(page)) ?? bookingRoot ?? page;
      console.log(`[AGENDAPRO][FLOW] ${target.name} | click Agendar ahora x2`);
      const advanced = await advanceBookingFlow(postEntryRoot);
      console.log(`[AGENDAPRO][FLOW] ${target.name} | Agendar flow=${advanced}`);
      console.log(`[AGENDAPRO][FLOW] ${target.name} | click Ver todas las fechas disponibles`);
      opened = await clickShowAllDates(postEntryRoot);
      console.log(`[AGENDAPRO][FLOW] ${target.name} | show all clicked=${opened}`);
      if (opened) {
        await settleAfterAction(postEntryRoot, 1_000);
      }
    }

    const activeRoot = (await resolveBookingRoot(page)) ?? bookingRoot ?? page;
    const bookingText = await collectBookingText(activeRoot);
    const candidateSignals = await collectBookingSignals(activeRoot);
    const buttonSnapshot = await collectButtonSnapshot(activeRoot);
    const frameSnapshot = await collectFrameSnapshot(page);
    const dates = extractDates(candidateSignals.length ? candidateSignals.join('\n') : bookingText);
    const times = extractTimes(candidateSignals.length ? candidateSignals.join('\n') : bookingText);

    if (dates.length || times.length) {
      return { status: 'OPEN', dates, times, reason: opened ? 'expanded_dates' : 'has_slots_text' };
    }

    if (isFullText(bookingText) || hasBookingMarkers(bookingText)) {
      return { status: 'FULL', dates: [], times: [], reason: 'no_availability_text' };
    }

    console.log(
      `[AGENDAPRO][DEBUG] ${target.name} | root=${bookingRoot === page ? 'page' : 'frame'} | signals=${candidateSignals.slice(0, 8).join(' || ') || '-'} | buttons=${buttonSnapshot.slice(0, 12).join(' || ') || '-'} | frames=${frameSnapshot.join(' || ') || '-'} | text=${bookingText.slice(0, 500).replace(/\s+/g, ' ')}`,
    );

    return { status: 'UNKNOWN', dates: [], times: [], reason: 'unclassified_page' };
  } catch (error) {
    return {
      status: 'ERROR',
      dates: [],
      times: [],
      reason: error instanceof Error ? error.message : String(error),
    };
  }
}

async function clickShowAllDates(page) {
  const candidates = [
    page.getByRole('button', { name: /Ver todas las fechas disponibles/i }),
    page.getByText(/Ver todas las fechas disponibles/i),
    page.locator('button', { hasText: /Ver todas las fechas disponibles/i }),
  ];

  for (const locator of candidates) {
    try {
      const resolved = locator.first();
      if ((await resolved.count().catch(() => 0)) === 0) {
        continue;
      }
      await resolved.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
      await resolved.click({ timeout: 1_500, noWaitAfter: true });
      return true;
    } catch {
      // keep trying the next locator
    }
  }

  return false;
}

async function clickVerHorario(root) {
  const candidates = [
    root.getByRole?.('button', { name: /Ver horario/i }),
    root.getByRole?.('link', { name: /Ver horario/i }),
    root.getByText?.(/Ver horario/i),
    root.locator?.('button', { hasText: /Ver horario/i }),
    root.locator?.('a', { hasText: /Ver horario/i }),
  ];

  for (const locator of candidates) {
    if (!locator) {
      continue;
    }

    try {
      const resolved = locator.first();
      if ((await resolved.count().catch(() => 0)) === 0) {
        continue;
      }
      await resolved.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
      await resolved.click({ timeout: 1_500, noWaitAfter: true });
      return true;
    } catch {
      // keep trying the next locator
    }
  }

  return false;
}

async function clickAgendarServicio(root) {
  const candidates = [
    root.getByRole?.('button', { name: /Agendar servicio/i }),
    root.getByRole?.('link', { name: /Agendar servicio/i }),
    root.getByText?.(/Agendar servicio/i),
    root.locator?.('button', { hasText: /Agendar servicio/i }),
    root.locator?.('a', { hasText: /Agendar servicio/i }),
  ];

  for (const locator of candidates) {
    if (!locator) {
      continue;
    }

    try {
      const resolved = locator.first();
      if ((await resolved.count().catch(() => 0)) === 0) {
        continue;
      }
      await resolved.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
      await resolved.click({ timeout: 1_500, noWaitAfter: true });
      return true;
    } catch {
      // keep trying the next locator
    }
  }

  return false;
}

async function collectBookingText(root) {
  try {
    const raw = await root.locator('body').innerText({ timeout: 5_000 }).catch(() => '');
    return normalizeTextWithLines(raw);
  } catch {
    return '';
  }
}

async function collectBookingSignals(root) {
  try {
    const rawSignals = await root
      .locator('button, a, [role="button"], [aria-label], [title], input[type="button"]')
      .evaluateAll((elements) =>
        elements.map((element) => {
          const parts = [
            element.getAttribute('aria-label'),
            element.getAttribute('title'),
            element.textContent,
          ]
            .filter(Boolean)
            .map((value) => String(value).replace(/\s+/g, ' ').trim())
            .filter(Boolean);
          return parts.join(' | ');
        }),
      )
      .catch(() => []);

    return rawSignals
      .map((value) => collapseWhitespace(String(value)))
      .filter((value) => value && !isUiNoiseText(value))
      .filter((value) => looksLikeDateSignal(value) || looksLikeTimeSignal(value));
  } catch {
    return [];
  }
}

async function collectButtonSnapshot(root) {
  try {
    const rawButtons = await root
      .locator('button, a, [role="button"], [aria-label], [title], input[type="button"], input[type="submit"]')
      .evaluateAll((elements) =>
        elements.map((element) => {
          const parts = [
            element.getAttribute('aria-label'),
            element.getAttribute('title'),
            element.textContent,
          ]
            .filter(Boolean)
            .map((value) => String(value).replace(/\s+/g, ' ').trim())
            .filter(Boolean);
          return parts.join(' | ');
        }),
      )
      .catch(() => []);

    return rawButtons.map((value) => collapseWhitespace(String(value))).filter(Boolean);
  } catch {
    return [];
  }
}

async function collectFrameSnapshot(page) {
  try {
    const frames = page.frames().slice(0, 8);
    const snapshot = [];
    for (const frame of frames) {
      const label = frame === page.mainFrame() ? 'main' : `depth${getFrameDepth(frame)}`;
      const body = collapseWhitespace(await frame.locator('body').innerText({ timeout: 2_000 }).catch(() => ''));
      if (!body) {
        continue;
      }
      snapshot.push(`${label}:${frame.url().slice(0, 80)}:${body.slice(0, 140)}`);
    }
    return snapshot;
  } catch {
    return [];
  }
}

async function resolveBookingRoot(page) {
  const candidates = [];
  for (const frame of page.frames()) {
    try {
      const hasAgendar = await frame.getByText(/Agendar ahora/i).first().isVisible().catch(() => false);
      const hasShowAll = await frame.getByText(/Ver todas las fechas disponibles/i).first().isVisible().catch(() => false);
      const bodyText = collapseWhitespace(await frame.locator('body').innerText({ timeout: 2_500 }).catch(() => ''));
      const textLower = bodyText.toLowerCase();
      const hasNoHours = textLower.includes('no hay horas disponibles');
      const hasSelect = textLower.includes('selecciona fecha y hora de tu servicio');
      const hasBookingNoise = textLower.includes('ver sucursal');

      if (hasAgendar || hasShowAll || hasNoHours || hasSelect) {
        let score = 0;
        if (hasAgendar) score += 5;
        if (hasShowAll) score += 4;
        if (hasNoHours) score += 3;
        if (hasSelect) score += 2;
        if (hasBookingNoise) score -= 1;
        score += Math.min(getFrameDepth(frame), 5);
        candidates.push({ frame, score });
      }
    } catch {
      // try next frame
    }
  }

  if (candidates.length > 0) {
    candidates.sort((left, right) => right.score - left.score);
    return candidates[0].frame;
  }

  return page;
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

async function advanceBookingFlow(root) {
  const firstClick = await clickAgendarAhora(root);
  if (!firstClick) {
    return false;
  }

  await settleAfterAction(root, 1_200);

  const page = getOwningPage(root);
  const refreshedRoot = page ? (await resolveBookingRoot(page)) ?? root : root;
  if (refreshedRoot !== root) {
    await settleAfterAction(refreshedRoot, 400);
  }

  const secondClick = await clickAgendarAhora(refreshedRoot);
  if (!secondClick && refreshedRoot !== root) {
    return await clickAgendarAhora(root);
  }

  await settleAfterAction(refreshedRoot, 1_200);
  return true;
}

async function clickAgendarAhora(root) {
  const candidates = [
    root.getByRole?.('button', { name: /Agendar ahora/i }),
    root.getByRole?.('link', { name: /Agendar ahora/i }),
    root.getByText?.(/Agendar ahora/i),
    root.locator?.('button', { hasText: /Agendar ahora/i }),
    root.locator?.('a', { hasText: /Agendar ahora/i }),
  ];

  for (const locator of candidates) {
    if (!locator) {
      continue;
    }

    try {
      const resolved = locator.first();
      if ((await resolved.count().catch(() => 0)) === 0) {
        continue;
      }
      await resolved.scrollIntoViewIfNeeded({ timeout: 1_000 }).catch(() => {});
      await resolved.click({ timeout: 1_500, noWaitAfter: true });
      return true;
    } catch {
      // keep trying the next locator
    }
  }

  return false;
}

async function settleAfterAction(root, waitMs) {
  if (typeof root.waitForTimeout === 'function') {
    await root.waitForTimeout(waitMs);
  } else if (typeof root.page === 'function') {
    await root.page().waitForTimeout(waitMs);
  }

  const page = typeof root.page === 'function' ? root.page() : null;
  if (page) {
    await page
      .waitForFunction(
        () => {
          const text = document.body?.innerText ?? '';
          const normalized = text.replace(/\s+/g, ' ').trim().toLowerCase();
          return (
            normalized.includes('no hay horas disponibles para esta selección'.toLowerCase()) ||
            normalized.includes('no hay horas disponibles') ||
            normalized.includes('ver todas las fechas disponibles'.toLowerCase()) ||
            normalized.includes('agendar ahora'.toLowerCase())
          );
        },
        { timeout: 5_000 },
      )
      .catch(() => {});
    await page.waitForTimeout(250);
  }
}

function extractDates(text) {
  const results = new Set();
  const lines = String(text)
    .split(/\r?\n+/)
    .map((line) => collapseWhitespace(line))
    .filter(Boolean);
  const patterns = [
    /\b(\d{1,2})\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b/gi,
    /\b(\d{1,2})[\/-](\d{1,2})(?:[\/-](\d{2,4}))?\b/g,
  ];

  for (const line of lines) {
    for (const pattern of patterns) {
      for (const match of line.matchAll(pattern)) {
        results.add(match[0].trim());
      }
    }
  }

  return [...results];
}

function extractTimes(text) {
  const results = new Set();
  const patterns = [
    /\b\d{1,2}:\d{2}\s?(?:a\.?\s?m\.?|p\.?\s?m\.?|AM|PM)?\b/gi,
    /\b\d{1,2}\s?(?:a\.?\s?m\.?|p\.?\s?m\.?|AM|PM)\b/gi,
  ];

  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern)) {
      results.add(match[0].replace(/\s+/g, ' ').trim());
    }
  }

  return [...results];
}

function looksLikeDateSignal(text) {
  const lowered = text.toLowerCase();
  return (
    /\b(\d{1,2})\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b/i.test(
      text,
    ) ||
    /\b(\d{1,2})[\/-](\d{1,2})(?:[\/-](\d{2,4}))?\b/.test(text) ||
    (/\b\d{1,2}\b/.test(text) && /\b(?:ene|feb|mar|abr|may|jun|jul|ago|sep|set|oct|nov|dic)\b/i.test(lowered))
  );
}

function looksLikeTimeSignal(text) {
  return /\b\d{1,2}:\d{2}\s?(?:a\.?\s?m\.?|p\.?\s?m\.?|AM|PM)?\b/i.test(text) || /\b\d{1,2}\s?(?:a\.?\s?m\.?|p\.?\s?m\.?|AM|PM)\b/i.test(text);
}

function isUiNoiseText(text) {
  const lowered = String(text).toLowerCase();
  return [
    'agendar ahora',
    'ver sucursal',
    'ver todas las fechas disponibles',
    'selecciona fecha y hora de tu servicio',
    'no hay horas disponibles para esta selección',
    'términos y condiciones',
    'terminos y condiciones',
    'iniciar sesión',
    'desarrollado por',
    'prueba gratis',
    'ver horario',
    'mesa 3',
    'cita',
    'otros',
    'servicio',
    'siguiente',
  ].some((phrase) => lowered.includes(phrase));
}

function isFullText(text) {
  const lowered = text.toLowerCase();
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

function hasBookingMarkers(text) {
  const lowered = text.toLowerCase();
  return [
    'agendar ahora',
    'ver todas las fechas disponibles',
    'selecciona fecha y hora de tu servicio',
    'fecha y hora',
    'no hay horas disponibles para esta selección',
  ].some((phrase) => lowered.includes(phrase));
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

function buildEvent(target, prev, curr, changedAt) {
  const prevDates = Array.isArray(prev?.dates) ? prev.dates : [];
  const prevTimes = Array.isArray(prev?.times) ? prev.times : [];
  const currDates = Array.isArray(curr.dates) ? curr.dates : [];
  const currTimes = Array.isArray(curr.times) ? curr.times : [];

  if (curr.status === 'ERROR') {
    return {
      target: target.name,
      url: target.url,
      prevStatus: prev?.status ?? null,
      currStatus: curr.status,
      prevSlots: prevDates,
      currSlots: currDates,
      changedAt,
      reason: 'error',
      detail: curr.reason ?? null,
    };
  }

  if (!prev) {
    return null;
  }

  if (prev.status !== curr.status) {
    return {
      target: target.name,
      url: target.url,
      prevStatus: prev?.status ?? null,
      currStatus: curr.status,
      prevSlots: prevDates,
      currSlots: currDates,
      changedAt,
      reason: 'status_changed',
      detail: curr.reason ?? null,
    };
  }

  if (curr.status === 'OPEN' && (!sameList(prevDates, currDates) || !sameList(prevTimes, currTimes))) {
    return {
      target: target.name,
      url: target.url,
      prevStatus: prev?.status ?? null,
      currStatus: curr.status,
      prevSlots: prevDates,
      currSlots: currDates,
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

function getTargetRecord(snapshots, targetName) {
  const existing = snapshots.get(targetName);
  if (existing && typeof existing === 'object') {
    if ('current' in existing) {
      return existing;
    }

    const migrated = {
      current: {
        status: existing.status ?? 'UNKNOWN',
        dates: Array.isArray(existing.dates) ? existing.dates : [],
        times: Array.isArray(existing.times) ? existing.times : [],
        updatedAt: existing.updatedAt ?? null,
        roundId: Number.isFinite(existing.roundId) ? existing.roundId : 0,
      },
    };
    snapshots.set(targetName, migrated);
    return migrated;
  }

  const created = {};
  snapshots.set(targetName, created);
  return created;
}

function getTargetSnapshot(targetRecord) {
  return targetRecord.current ?? null;
}

function setTargetSnapshot(targetRecord, nextSnapshot) {
  targetRecord.current = nextSnapshot;
}

function validateTargets(list) {
  if (list.length === 0) {
    throw new Error('targets must contain at least 1 entry');
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

async function writeAlertFile(event) {
  try {
    await fs.promises.mkdir(path.dirname(ALERT_FILE_PATH), { recursive: true }).catch(() => {});
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
    await fs.promises.writeFile(ALERT_FILE_PATH, `${summary}\n`, 'utf8');
  } catch (error) {
    console.log(`[AGENDAPRO] unable to write alert file | ${error instanceof Error ? error.message : String(error)}`);
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
        text: formatTelegramMessage(event),
        disable_web_page_preview: 'true',
      }),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[AGENDAPRO][WARN] telegram push failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[AGENDAPRO][WARN] telegram push error | ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

function formatTelegramMessage(event) {
  const dates = Array.isArray(event.currSlots) ? event.currSlots : [];
  const dateSummary =
    dates.length === 0
      ? '-'
      : dates.length <= 5
        ? dates.join(', ')
        : `${dates.slice(0, 5).join(', ')} … 共${dates.length}个时段`;

  return [
    `AgendaPro 状态：${event.currStatus}`,
    `目标：${event.target}`,
    `原因：${event.reason}`,
    `时间：${event.changedAt}`,
    ...(event.prevStatus ? [`上次状态：${event.prevStatus}`] : []),
    ...(event.currStatus === 'OPEN' ? [`可预约时段：${dateSummary}`] : []),
    `链接：${event.url}`,
  ].join('\n');
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
  } catch {
    return { targets: {} };
  }
}

function saveState(filePath, data) {
  const tempPath = `${filePath}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
  fs.renameSync(tempPath, filePath);
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

function collapseWhitespace(value) {
  return value.replace(/\s+/g, ' ').trim();
}

function getOwningPage(root) {
  if (root && typeof root.page === 'function') {
    return root.page();
  }

  return root ?? null;
}

function normalizeTextWithLines(value) {
  return String(value)
    .replace(/\r/g, '')
    .split('\n')
    .map((line) => collapseWhitespace(line))
    .filter(Boolean)
    .join('\n');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

await main().catch((error) => {
  console.error(`[FATAL] ${error instanceof Error ? error.stack || error.message : String(error)}`);
  process.exitCode = 1;
});
