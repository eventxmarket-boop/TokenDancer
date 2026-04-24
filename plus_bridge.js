#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

loadEnvFile(path.join(__dirname, '.env'));

const args = parseArgs(process.argv.slice(2));
const CHAT_URL = args.chatUrl || process.env.PLUS_BRIDGE_CHAT_URL || 'https://chatgpt.com/';
const USER_DATA_DIR = path.resolve(
  __dirname,
  args.userDataDir || process.env.PLUS_BRIDGE_USER_DATA_DIR || '.plus_bridge_profile',
);
const OUTPUT_DIR = path.resolve(
  __dirname,
  args.outputDir || process.env.PLUS_BRIDGE_OUTPUT_DIR || '.plus_bridge_output',
);
const UPLOAD_URL = args.uploadUrl || process.env.PLUS_BRIDGE_UPLOAD_URL || '';
const HEADLESS = parseBoolean(args.headless ?? process.env.PLUS_BRIDGE_HEADLESS, false);
const WAIT_MS = parseInteger(args.waitMs ?? process.env.PLUS_BRIDGE_WAIT_MS, 300000);
const SCREENSHOT_TIMEOUT_MS = parseInteger(
  args.screenshotTimeoutMs ?? process.env.PLUS_BRIDGE_SCREENSHOT_TIMEOUT_MS,
  120000,
);

const PROMPT = args.prompt || readPromptFile(args.promptFile || process.env.PLUS_BRIDGE_PROMPT_FILE);
const MODE = args.bootstrap ? 'bootstrap' : PROMPT ? 'generate' : 'help';

if (args.help || MODE === 'help') {
  printHelp();
  process.exit(MODE === 'help' ? 1 : 0);
}

await fs.promises.mkdir(OUTPUT_DIR, { recursive: true }).catch(() => {});

const browserContext = await chromium.launchPersistentContext(USER_DATA_DIR, {
  headless: HEADLESS,
  viewport: { width: 1440, height: 1280 },
});

const page = browserContext.pages()[0] || (await browserContext.newPage());

try {
  await page.goto(CHAT_URL, { waitUntil: 'domcontentloaded' });

  if (MODE === 'bootstrap') {
    console.log(`[PLUS-BRIDGE] Browser opened at ${CHAT_URL}`);
    console.log('[PLUS-BRIDGE] 请先在浏览器里完成 ChatGPT 登录。登录后回到终端按回车结束本次 bootstrap。');
    await waitForEnter();
    await writeExitNotice({ mode: 'bootstrap' });
    process.exit(0);
  }

  const composer = await waitForComposer(page, WAIT_MS);
  const beforeImageCount = await page.locator('main img, article img, img').count().catch(() => 0);
  await sendPrompt(page, composer, PROMPT);

  const imageCandidate = await waitForAssistantImage(page, beforeImageCount, SCREENSHOT_TIMEOUT_MS);
  const imageCapture = await captureImageArtifact(page, imageCandidate);

  const result = {
    prompt: PROMPT,
    prompt_length: PROMPT.trim().length,
    model: 'chatgpt-plus-bridge',
    size: args.size || 'unknown',
    quality: args.quality || 'unknown',
    output_format: args.outputFormat || 'png',
    source: 'chatgpt-plus',
    page_url: page.url(),
    captured_at: new Date().toISOString(),
    image_base64: imageCapture.imageBase64,
    mime_type: imageCapture.mimeType,
    image_source: imageCandidate.src,
  };

  const resultPath = path.join(
    OUTPUT_DIR,
    `plus-bridge-${new Date().toISOString().replace(/[:.]/g, '-')}.json`,
  );
  await fs.promises.writeFile(resultPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');

  if (UPLOAD_URL) {
    try {
      const uploadResponse = await fetch(UPLOAD_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(result),
      });
      if (!uploadResponse.ok) {
        const detail = await uploadResponse.text().catch(() => '');
        console.log(
          `[PLUS-BRIDGE] upload failed | status=${uploadResponse.status} | ${detail.trim() || 'no response body'}`,
        );
      } else {
        console.log(`[PLUS-BRIDGE] uploaded to ${UPLOAD_URL}`);
      }
    } catch (error) {
      console.log(
        `[PLUS-BRIDGE] upload error | ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }

  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(`[PLUS-BRIDGE] ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
} finally {
  await browserContext.close().catch(() => {});
}

function printHelp() {
  console.log([
    'Usage:',
    '  node plus_bridge.js --prompt "a cat in a paper crown" [--upload-url http://127.0.0.1:8011/persona-api/image-lab/bridge/submit]',
    '  node plus_bridge.js --bootstrap',
    '',
    'Flags:',
    '  --prompt <text>                生成提示词',
    '  --prompt-file <path>           从文件读取提示词',
    '  --upload-url <url>             生成后把结果上传到服务器',
    '  --chat-url <url>               ChatGPT 入口地址，默认 https://chatgpt.com/',
    '  --user-data-dir <path>         Chromium 持久化用户目录',
    '  --output-dir <path>            输出 JSON 所在目录',
    '  --headless true|false          是否无头，默认 false',
    '  --wait-ms <number>             等待登录/输入框的总时长',
    '  --screenshot-timeout-ms <num>   等待图片出现的时长',
    '  --bootstrap                    仅打开浏览器并等待手工登录',
    '',
    'Environment:',
    '  PLUS_BRIDGE_CHAT_URL',
    '  PLUS_BRIDGE_USER_DATA_DIR',
    '  PLUS_BRIDGE_OUTPUT_DIR',
    '  PLUS_BRIDGE_UPLOAD_URL',
    '  PLUS_BRIDGE_HEADLESS',
    '  PLUS_BRIDGE_WAIT_MS',
    '  PLUS_BRIDGE_SCREENSHOT_TIMEOUT_MS',
    '  PLUS_BRIDGE_PROMPT_FILE',
  ].join('\n'));
}

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith('--')) {
      continue;
    }

    const [keyPart, inlineValue] = arg.slice(2).split('=', 2);
    const key = toCamelCase(keyPart);

    if (key === 'help' || key === 'bootstrap') {
      parsed[key] = true;
      continue;
    }

    const next = inlineValue ?? argv[index + 1];
    if (inlineValue === undefined && next && !String(next).startsWith('--')) {
      parsed[key] = next;
      index += 1;
    } else if (inlineValue !== undefined) {
      parsed[key] = inlineValue;
    } else {
      parsed[key] = true;
    }
  }
  return parsed;
}

function toCamelCase(value) {
  return value.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
}

function parseBoolean(value, fallback) {
  if (value === undefined || value === null || value === '') {
    return fallback;
  }
  const normalized = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'y'].includes(normalized)) return true;
  if (['0', 'false', 'no', 'n'].includes(normalized)) return false;
  return fallback;
}

function parseInteger(value, fallback) {
  const parsed = Number.parseInt(String(value ?? '').trim(), 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function loadEnvFile(envPath) {
  if (!fs.existsSync(envPath)) {
    return;
  }

  const text = fs.readFileSync(envPath, 'utf8');
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) {
      continue;
    }

    const eqIndex = trimmed.indexOf('=');
    const key = trimmed.slice(0, eqIndex).trim();
    let value = trimmed.slice(eqIndex + 1).trim();

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

function readPromptFile(filePath) {
  if (!filePath) {
    return '';
  }

  const resolved = path.resolve(__dirname, filePath);
  if (!fs.existsSync(resolved)) {
    return '';
  }

  return fs.readFileSync(resolved, 'utf8').trim();
}

async function waitForEnter() {
  process.stdin.setEncoding('utf8');
  process.stdin.resume();

  await new Promise((resolve) => {
    process.stdin.once('data', () => resolve(null));
  });
}

async function waitForComposer(page, timeoutMs) {
  const selectors = [
    'textarea',
    '[contenteditable="true"][role="textbox"]',
    '[contenteditable="true"]',
  ];

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const selector of selectors) {
      const locator = page.locator(selector).first();
      try {
        if (await locator.count()) {
          await locator.waitFor({ state: 'visible', timeout: 1000 });
          return locator;
        }
      } catch {
        // keep polling
      }
    }

    const pageText = await page.locator('body').innerText({ timeout: 1000 }).catch(() => '');
    if (/(log in|sign in|登录|登入|继续|continue)/i.test(pageText)) {
      console.log('[PLUS-BRIDGE] 等待你在浏览器里登录 ChatGPT...');
    }
    await page.waitForTimeout(1000);
  }

  throw new Error('未找到 ChatGPT 输入框，请先完成登录后重试。');
}

async function sendPrompt(page, composer, prompt) {
  await composer.click({ timeout: 5000 }).catch(() => {});
  const tagName = await composer.evaluate((element) => element.tagName.toLowerCase()).catch(() => '');

  if (tagName === 'textarea' || tagName === 'input') {
    await composer.fill(prompt);
  } else {
    await page.keyboard.insertText(prompt);
  }

  await page.keyboard.press('Enter');
}

async function waitForAssistantImage(page, previousCount, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let stableSignature = '';
  let stableRounds = 0;

  while (Date.now() < deadline) {
    const snapshot = await page.evaluate(({ baseline }) => {
      const allImages = Array.from(document.querySelectorAll('img'));
      return allImages
        .map((img, index) => {
          const rect = img.getBoundingClientRect();
          const rawText = [
            img.alt || '',
            img.title || '',
            img.getAttribute('aria-label') || '',
            img.closest('article')?.innerText || '',
            img.closest('[data-message-author-role="assistant"]')?.innerText || '',
          ]
            .join(' ')
            .trim()
            .toLowerCase();
          const src = img.currentSrc || img.src || '';
          const width = Math.round(rect.width || img.width || 0);
          const height = Math.round(rect.height || img.height || 0);
          return { index, src, width, height, rawText, baseline };
        })
        .filter((item) => {
          if (!item.src) return false;
          if (item.index < baseline) return false;
          if (item.width < 96 || item.height < 96) return false;
          if (/(logo|avatar|spinner|icon|openai|chatgpt)/i.test(`${item.rawText} ${item.src}`)) {
            return false;
          }
          return true;
        });
    }, { baseline: previousCount });

    if (snapshot.length) {
      const candidate = snapshot[snapshot.length - 1];
      const signature = `${candidate.src}|${candidate.width}x${candidate.height}`;
      if (signature === stableSignature) {
        stableRounds += 1;
      } else {
        stableSignature = signature;
        stableRounds = 1;
      }

      if (stableRounds >= 2) {
        return candidate;
      }
    }

    await page.waitForTimeout(2000);
  }

  throw new Error('没有检测到可用图片结果，可能需要手动确认 ChatGPT 是否完成了生图。');
}

async function captureImageArtifact(page, candidate) {
  const imageLocator = page.locator('img').nth(candidate.index);

  const extracted = await extractImageBase64FromSrc(page, candidate.src).catch(() => null);
  if (extracted) {
    return extracted;
  }

  const fallbackPath = path.join(
    OUTPUT_DIR,
    `plus-bridge-fallback-${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
  );
  await imageLocator.screenshot({ path: fallbackPath });
  return {
    imageBase64: fs.readFileSync(fallbackPath).toString('base64'),
    mimeType: 'image/png',
  };
}

async function extractImageBase64FromSrc(page, src) {
  if (!src) {
    return null;
  }

  if (src.startsWith('data:')) {
    const match = /^data:([^;]+);base64,(.+)$/s.exec(src);
    if (!match) {
      return null;
    }

    return {
      mimeType: match[1],
      imageBase64: match[2],
    };
  }

  if (src.startsWith('blob:') || src.startsWith('http://') || src.startsWith('https://')) {
    try {
      return await page.evaluate(async (imageSrc) => {
        const response = await fetch(imageSrc);
        const blob = await response.blob();
        const bytes = new Uint8Array(await blob.arrayBuffer());
        const chunkSize = 0x8000;
        let binary = '';
        for (let index = 0; index < bytes.length; index += chunkSize) {
          const chunk = bytes.subarray(index, index + chunkSize);
          binary += String.fromCharCode(...chunk);
        }
        return {
          mimeType: blob.type || response.headers.get('content-type') || 'image/png',
          imageBase64: btoa(binary),
        };
      }, src);
    } catch {
      return null;
    }
  }

  return null;
}

async function writeExitNotice(details) {
  const noticePath = path.join(OUTPUT_DIR, 'plus-bridge-last-run.json');
  const payload = {
    mode: details.mode,
    finishedAt: new Date().toISOString(),
  };
  await fs.promises.writeFile(noticePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}
