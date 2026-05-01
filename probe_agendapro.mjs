import { chromium } from 'playwright';

const url = 'https://fundacionibn.site.agendapro.com/es/sucursal/497344/profesional/810124';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  page.setDefaultTimeout(45000);
  page.setDefaultNavigationTimeout(45000);
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(750);
  console.log('URL after goto:', page.url());
  const text0 = await page.locator('body').innerText().catch(() => '');
  console.log('BODY0:', text0.slice(0, 2500));
  const frames = page.frames();
  console.log('FRAMES:', frames.length);
  for (let i = 0; i < frames.length; i += 1) {
    const frame = frames[i];
    const body = await frame.locator('body').innerText().catch(() => '');
    console.log(`FRAME ${i} URL:`, frame.url());
    console.log(`FRAME ${i} BODY:`, body.slice(0, 1500));
  }
} finally {
  await browser.close();
}
