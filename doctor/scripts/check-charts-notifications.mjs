import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
import { readFile, mkdir } from 'node:fs/promises';
import vm from 'node:vm';

const base = process.env.PREVIEW_URL ?? 'http://127.0.0.1:5173';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const context = await browser.newContext({ permissions: ['notifications'], reducedMotion: 'reduce' });
const page = await context.newPage();
const errors = [];
page.on('pageerror', error => errors.push(error.message));
let notices = [], subscribePayload, unsubscribePayload, registeredPath, markReads = 0;
const token = 'isolated-notification-token';
const user = { id: 'doc-chart-test', public_id: 'D_TEST', full_name: 'Dr Chart Preview', email: 'doctor@example.com', phone_number: '+919876543210', role: 'DOCTOR', approval_status: 'APPROVED', doctor: { qualification: 'MBBS', registering_council: 'Delhi Medical Council', medical_registration_number: 'REG123', years_of_experience: 4, clinic_address: 'Example Clinic', address: 'Example Address' } };
const date = new Date().toISOString();
await page.addInitScript(() => {
  let subscription = null, registered = false;
  const registration = { pushManager: { getSubscription: async () => subscription, subscribe: async options => {
    window.__pushKeyLength = options.applicationServerKey.length;
    subscription = { endpoint: 'https://fcm.googleapis.com/fcm/send/isolated-browser-test', toJSON: () => ({ endpoint: 'https://fcm.googleapis.com/fcm/send/isolated-browser-test', keys: { auth: 'isolated-auth', p256dh: 'isolated-public-key' } }), unsubscribe: async () => { subscription = null; return true; } }; return subscription;
  } } };
  navigator.serviceWorker.register = async (path, options) => { window.__registeredPushWorker = { path, scope: options.scope }; registered = true; return registration; };
  navigator.serviceWorker.getRegistration = async () => registered ? registration : undefined;
  Object.defineProperty(navigator.serviceWorker, 'ready', { get: () => Promise.resolve(registration) });
});
await page.route('**/api/v1/**', async route => {
  const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '');
  if (path === '/doctors/me') return route.fulfill({ json: { user, notification_token: token } });
  if (path === '/doctors/care-profiles') return route.fulfill({ json: { items: [{ id: 'p1', full_name: 'Shared Preview', module: 'child', created_at: date }], total: 1 } });
  if (path === '/doctors/consultation-requests') return route.fulfill({ json: { items: [{ id: 'request', child_id: 'p1', title: 'Request preview', date: date.slice(0, 10), status: 'REQUESTED' }], total: 1 } });
  if (path.startsWith('/doctors/notifications')) {
    assert.equal(request.headers().authorization, `Bearer ${token}`);
    if (path.endsWith('/push-config')) return route.fulfill({ json: { enabled: true, public_key: Buffer.from([4, ...Array(64).fill(1)]).toString('base64url') } });
    if (path.endsWith('/subscriptions')) {
      if (request.method() === 'POST') subscribePayload = request.postDataJSON(); else unsubscribePayload = request.postDataJSON();
      return route.fulfill({ status: request.method() === 'POST' ? 201 : 200, json: { message: 'Saved in isolated mock' } });
    }
    if (path.endsWith('/read')) { markReads++; notices = notices.map(notice => ({ ...notice, read_at: date })); return route.fulfill({ json: { message: 'Read' } }); }
    return route.fulfill({ json: { items: notices, unread: notices.filter(notice => !notice.read_at).length, total: notices.length } });
  }
  return route.fulfill({ status: 404, json: { error: { message: 'Not part of this isolated test' } } });
});
try {
  await mkdir('app/.preview', { recursive: true });
  await page.goto(base + '/doctor/dashboard');
  await expect(page.getByRole('heading', { name: 'Doctor Dashboard', exact: true })).toBeVisible();
  await expect(page.locator('.doctor-chart-card canvas')).toHaveCount(3);
  for (const width of [390, 1366, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: `app/.preview/doctor-charts-${width}.png`, fullPage: true });
  }
  await page.getByRole('navigation', { name: 'Doctor workspace' }).getByRole('link', { name: 'Patients', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Patients', exact: true })).toBeVisible();
  notices = [{ id: 'notice1', kind: 'consultation_requested', title: 'New consultation request', body: 'A connected family has requested a consultation.', path: '/doctor/consultations', created_at: date, read_at: null }];
  await page.evaluate(() => navigator.serviceWorker.dispatchEvent(new MessageEvent('message', { data: { type: 'doctor-push', id: 'notice1' } })));
  await expect(page.getByRole('status')).toContainText('New consultation request');
  await expect(page.getByRole('button', { name: 'Notifications (1 unread)', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Open notification →' }).click();
  await expect(page).toHaveURL(base + '/doctor/consultations');
  await expect(page.getByRole('heading', { name: 'Consultations', exact: true })).toBeVisible();
  assert.equal(markReads, 1);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Notifications', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Enable notifications', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Disable on this device', exact: true })).toBeVisible();
  registeredPath = await page.evaluate(() => window.__registeredPushWorker);
  assert.deepEqual(registeredPath, { path: '/doctor-sw.js', scope: '/doctor/' });
  assert.equal(await page.evaluate(() => window.__pushKeyLength), 65);
  assert.equal(subscribePayload.endpoint, 'https://fcm.googleapis.com/fcm/send/isolated-browser-test');
  await page.getByRole('button', { name: 'Disable on this device', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Enable notifications', exact: true })).toBeVisible();
  assert.equal(unsubscribePayload.endpoint, subscribePayload.endpoint);
  assert.equal(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }).includes('isolated-notification-token')), false);
  assert.deepEqual(errors, []);
  console.log('PASS three Chart.js chart types, responsive sizes, cross-page inbox/toast, read/navigation, opt-in/out and memory-only notification token. Mock push service; no real notifications sent.');

  // Exercise push and notification-click handlers without contacting a push provider or showing OS UI.
  const listeners = {}, shown = [], focused = [];
  const sandbox = { URL, self: { location: { origin: base }, skipWaiting() {}, addEventListener: (type, handler) => { listeners[type] = handler; },
    registration: { showNotification: async (title, options) => shown.push({ title, options }) },
    clients: { claim: async () => {}, matchAll: async () => [{ url: base + '/doctor/patients', postMessage() {}, navigate: async url => focused.push(url), focus: async () => {} }], openWindow: async url => focused.push(url) } } };
  vm.runInNewContext(await readFile('app/public/doctor-sw.js', 'utf8'), sandbox);
  let done;
  listeners.push({ data: { json: () => ({ id: 'test-push', title: 'Account update', body: 'Open FamilyCare+ for details.', path: '/doctor/reports' }) }, waitUntil: promise => { done = promise; } });
  await done;
  assert.equal(shown[0].options.tag, 'familycare-doctor-test-push');
  listeners.notificationclick({ notification: { close() {}, data: { path: 'https://untrusted.invalid/private' } }, waitUntil: promise => { done = promise; } });
  await done;
  assert.equal(focused[0], base + '/doctor/dashboard');
  console.log('PASS service worker background notification handler and same-origin click protection.');
} finally { await browser.close(); }
 