#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
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
const STATUS_URL = args.statusUrl || process.env.PLUS_BRIDGE_STATUS_URL || '';
const HEADLESS = parseBoolean(args.headless ?? process.env.PLUS_BRIDGE_HEADLESS, false);
const TRANSPORT = String(args.transport || process.env.PLUS_BRIDGE_TRANSPORT || 'persistent')
  .trim()
  .toLowerCase();
const CDP_ENDPOINT = String(args.cdpEndpoint || process.env.PLUS_BRIDGE_CDP_ENDPOINT || '')
  .trim();
const CDP_USER_DATA_DIR = path.resolve(
  __dirname,
  args.cdpUserDataDir || process.env.PLUS_BRIDGE_CDP_USER_DATA_DIR || '.plus_bridge_cdp_profile',
);
const CDP_LAUNCH = parseBoolean(args.cdpLaunch ?? process.env.PLUS_BRIDGE_CDP_LAUNCH, true);
const CDP_PORT = parseInteger(args.cdpPort ?? process.env.PLUS_BRIDGE_CDP_PORT, 9222);
const BROWSER_EXECUTABLE = String(
  args.browserExecutable || process.env.PLUS_BRIDGE_BROWSER_EXECUTABLE || chromium.executablePath(),
).trim();
const WAIT_MS = parseInteger(args.waitMs ?? process.env.PLUS_BRIDGE_WAIT_MS, 300000);
const SCREENSHOT_TIMEOUT_MS = parseInteger(
  args.screenshotTimeoutMs ?? process.env.PLUS_BRIDGE_SCREENSHOT_TIMEOUT_MS,
  120000,
);

const PROMPT = args.prompt || readPromptFile(args.promptFile || process.env.PLUS_BRIDGE_PROMPT_FILE);
const MODE = args.bootstrap ? 'bootstrap' : PROMPT ? 'generate' : 'help';
const RUNTIME_MODE = TRANSPORT === 'cdp' ? 'cdp' : 'persistent';

if (args.help || MODE === 'help') {
  printHelp();
  process.exit(MODE === 'help' ? 1 : 0);
}

await fs.promises.mkdir(OUTPUT_DIR, { recursive: true }).catch(() => {});

const browserSession = await createBrowserSession({
  transport: RUNTIME_MODE,
  headless: HEADLESS,
  userDataDir: TRANSPORT === 'cdp' ? CDP_USER_DATA_DIR : USER_DATA_DIR,
  cdpEndpoint: CDP_ENDPOINT,
  cdpLaunch: CDP_LAUNCH,
  cdpPort: CDP_PORT,
  browserExecutable: BROWSER_EXECUTABLE,
});
const browserContext = browserSession.context;
const page = browserContext.pages()[0] || (await browserContext.newPage());

try {
  await page.goto(CHAT_URL, { waitUntil: 'domcontentloaded' });
  await emitBridgeEvent('page_opened', '浏览器已打开聊天页面', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
  });

  if (MODE === 'bootstrap') {
    console.log(`[PLUS-BRIDGE] Browser opened at ${CHAT_URL}`);
    console.log('[PLUS-BRIDGE] 请先在浏览器里完成 ChatGPT 登录。登录后回到终端按回车结束本次 bootstrap。');
    await emitBridgeEvent('bootstrap_waiting', '等待手工登录 ChatGPT', {
      mode: MODE,
      transport: RUNTIME_MODE,
      pageUrl: page.url(),
    });
    await waitForEnter();
    await emitBridgeEvent('bootstrap_done', '手工登录窗口结束', {
      mode: MODE,
      transport: RUNTIME_MODE,
      pageUrl: page.url(),
      success: true,
    });
    await writeExitNotice({ mode: 'bootstrap' });
    process.exit(0);
  }

  const composer = await waitForComposer(page, WAIT_MS);
  await emitBridgeEvent('composer_ready', '输入框已就绪', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
  });
  const beforeImageCount = await page.locator('main img, article img, img').count().catch(() => 0);
  await emitBridgeEvent('prompt_sending', '开始发送提示词', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
  });
  await sendPrompt(page, composer, PROMPT);
  await emitBridgeEvent('prompt_sent', '提示词已发送，等待结果', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
  });

  await emitBridgeEvent('result_waiting', '等待图片结果', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
  });
  const imageCandidate = await waitForAssistantImage(page, beforeImageCount, SCREENSHOT_TIMEOUT_MS);
  await emitBridgeEvent('result_found', '已检测到图片结果', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
  });
  const imageCapture = await captureImageArtifact(page, imageCandidate);
  await emitBridgeEvent('result_captured', '图片已捕获', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
    mimeType: imageCapture.mimeType,
  });

  const result = {
    prompt: PROMPT,
    prompt_length: PROMPT.trim().length,
    model: 'chatgpt-plus-bridge',
    transport: RUNTIME_MODE,
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

  await emitBridgeEvent('result_ready', '结果已生成', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: page.url(),
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
    mimeType: imageCapture.mimeType,
    success: true,
  });

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
        await emitBridgeEvent('result_uploaded', '结果已上传到服务器', {
          mode: MODE,
          transport: RUNTIME_MODE,
          pageUrl: page.url(),
          prompt: PROMPT,
          promptLength: PROMPT.trim().length,
          mimeType: imageCapture.mimeType,
          success: true,
        });
      }
    } catch (error) {
      console.log(
        `[PLUS-BRIDGE] upload error | ${error instanceof Error ? error.message : String(error)}`,
      );
      await emitBridgeEvent('upload_failed', '结果上传失败', {
        mode: MODE,
        transport: RUNTIME_MODE,
        pageUrl: page.url(),
        prompt: PROMPT,
        promptLength: PROMPT.trim().length,
        error: error instanceof Error ? error.message : String(error),
        success: false,
      });
    }
  }

  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(`[PLUS-BRIDGE] ${error instanceof Error ? error.message : String(error)}`);
  await emitBridgeEvent('failed', '桥接执行失败', {
    mode: MODE,
    transport: RUNTIME_MODE,
    pageUrl: '',
    prompt: PROMPT,
    promptLength: PROMPT.trim().length,
    error: error instanceof Error ? error.message : String(error),
    success: false,
  }).catch(() => {});
  process.exitCode = 1;
} finally {
  await browserSession.cleanup().catch(() => {});
}

function printHelp() {
  console.log([
    'Usage:',
    '  node plus_bridge.js --prompt "a cat in a paper crown" [--upload-url http://127.0.0.1:8011/persona-api/image-lab/bridge/submit]',
    '  node plus_bridge.js --bootstrap',
    '  node plus_bridge.js --transport cdp --cdp-launch --prompt "a cat in a paper crown"',
    '  node plus_bridge.js --transport cdp --cdp-endpoint http://127.0.0.1:9222 --prompt "a cat in a paper crown"',
    '',
    'Flags:',
    '  --prompt <text>                生成提示词',
    '  --prompt-file <path>           从文件读取提示词',
    '  --upload-url <url>             生成后把结果上传到服务器',
    '  --status-url <url>             发送阶段状态到服务器',
    '  --chat-url <url>               ChatGPT 入口地址，默认 https://chatgpt.com/',
    '  --user-data-dir <path>         Chromium 持久化用户目录',
    '  --output-dir <path>            输出 JSON 所在目录',
    '  --headless true|false          是否无头，默认 false',
    '  --transport persistent|cdp     浏览器桥接模式，默认 persistent',
    '  --cdp-endpoint <url>           连接已有 Chrome CDP 端点',
    '  --cdp-launch true|false        是否自动启动 CDP Chrome，默认 true',
    '  --cdp-user-data-dir <path>     CDP 模式专用用户目录',
    '  --cdp-port <number>            自动启动时的调试端口',
    '  --browser-executable <path>     Chrome / Chromium 可执行文件',
    '  --wait-ms <number>             等待登录/输入框的总时长',
    '  --screenshot-timeout-ms <num>   等待图片出现的时长',
    '  --bootstrap                    仅打开浏览器并等待手工登录',
    '',
    'Environment:',
    '  PLUS_BRIDGE_CHAT_URL',
    '  PLUS_BRIDGE_USER_DATA_DIR',
    '  PLUS_BRIDGE_OUTPUT_DIR',
    '  PLUS_BRIDGE_UPLOAD_URL',
    '  PLUS_BRIDGE_STATUS_URL',
    '  PLUS_BRIDGE_HEADLESS',
    '  PLUS_BRIDGE_TRANSPORT',
    '  PLUS_BRIDGE_CDP_ENDPOINT',
    '  PLUS_BRIDGE_CDP_USER_DATA_DIR',
    '  PLUS_BRIDGE_CDP_LAUNCH',
    '  PLUS_BRIDGE_CDP_PORT',
    '  PLUS_BRIDGE_BROWSER_EXECUTABLE',
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

async function createBrowserSession({
  transport,
  headless,
  userDataDir,
  cdpEndpoint,
  cdpLaunch,
  cdpPort,
  browserExecutable,
}) {
  if (transport === 'cdp') {
    if (cdpEndpoint) {
      const browser = await chromium.connectOverCDP(cdpEndpoint);
      const context = browser.contexts()[0] || (await browser.newContext());
      return {
        browser,
        context,
        cleanup: async () => {},
      };
    }

    if (!cdpLaunch) {
      throw new Error('CDP 模式需要 --cdp-endpoint 或 --cdp-launch');
    }

    return launchCdpBrowser({
      browserExecutable,
      headless,
      userDataDir,
      cdpPort,
    });
  }

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless,
    viewport: { width: 1440, height: 1280 },
  });

  return {
    browser: context.browser(),
    context,
    cleanup: async () => {
      await context.close().catch(() => {});
    },
  };
}

async function launchCdpBrowser({ browserExecutable, headless, userDataDir, cdpPort }) {
  const executable = resolveBrowserExecutable(browserExecutable);
  if (!executable) {
    throw new Error('未找到 Chrome / Chromium 可执行文件，无法启动 CDP 模式。');
  }

  await fs.promises.mkdir(userDataDir, { recursive: true }).catch(() => {});

  const child = spawn(
    executable,
    [
      `--remote-debugging-port=${cdpPort}`,
      `--user-data-dir=${userDataDir}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-dev-shm-usage',
      ...(headless ? ['--headless=new'] : []),
    ],
    {
      detached: false,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );

  child.stdout.on('data', (chunk) => {
    process.stdout.write(`[PLUS-BRIDGE/CDP] ${chunk.toString()}`);
  });
  child.stderr.on('data', (chunk) => {
    process.stderr.write(`[PLUS-BRIDGE/CDP] ${chunk.toString()}`);
  });

  await waitForCdpEndpoint(cdpPort, WAIT_MS);

  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${cdpPort}`);
  const context = browser.contexts()[0] || (await browser.newContext());

  return {
    browser,
    context,
    cleanup: async () => {
      await context.close().catch(() => {});
      if (!child.killed) {
        child.kill('SIGTERM');
      }
    },
  };
}

function resolveBrowserExecutable(explicitExecutable) {
  const trimmed = String(explicitExecutable || '').trim();
  if (trimmed) {
    return trimmed;
  }

  const candidates = [
    chromium.executablePath(),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];

  return candidates.find((candidate) => candidate && fs.existsSync(candidate)) || '';
}

async function waitForCdpEndpoint(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  const endpoint = `http://127.0.0.1:${port}/json/version`;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(endpoint);
      if (response.ok) {
        const body = await response.json().catch(() => null);
        if (body && typeof body.webSocketDebuggerUrl === 'string') {
          return body;
        }
      }
    } catch {
      // keep polling
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  throw new Error(`CDP 端点在 ${timeoutMs}ms 内未就绪：${endpoint}`);
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

async function emitBridgeEvent(stage, message, extra = {}) {
  if (!STATUS_URL) {
    return null;
  }

  const payload = {
    stage,
    message,
    mode: extra.mode || MODE,
    transport: extra.transport || RUNTIME_MODE,
    prompt: extra.prompt || PROMPT,
    prompt_length: extra.promptLength ?? extra.prompt_length ?? PROMPT.trim().length,
    size: extra.size || args.size || 'unknown',
    quality: extra.quality || args.quality || 'unknown',
    output_format: extra.outputFormat || extra.output_format || args.outputFormat || 'png',
    success: extra.success,
    error: extra.error,
    page_url: extra.pageUrl || extra.page_url || '',
    mime_type: extra.mimeType || extra.mime_type || '',
    user_id: extra.userId || extra.user_id || '',
  };

  try {
    const response = await fetch(STATUS_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.log(
        `[PLUS-BRIDGE] status upload failed | status=${response.status} | ${detail.trim() || 'no response body'}`,
      );
    }
  } catch (error) {
    console.log(
      `[PLUS-BRIDGE] status upload error | ${error instanceof Error ? error.message : String(error)}`,
    );
  }

  return payload;
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
