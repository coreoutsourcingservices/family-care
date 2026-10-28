import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';

// Mock API replies only: this check creates no accounts and sends no emails.
const base = process.env.PREVIEW_URL || 'http://127.0.0.1:5173';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ reducedMotion: 'reduce' });
const errors = [];
const requests = [];
let authenticated = false;
let expireAccess = false;
let invalidOtp = false;
let restricted = false;
let networkFailure = false;
let registerConflict = false;
let resendDelay = 60;
page.on('pageerror', error => errors.push(error.message));
await page.route('**/api/v1/**', async route => {
  const req = route.request();
  const path = new URL(req.url()).pathname;
  const body = req.method() === 'POST' ? req.postDataJSON() : null;
  requests.push({ path, body, headers: req.headers() });
  assert.equal(req.method(), path.endsWith('/me') || path.endsWith('/care-profiles') || path.endsWith('/profiles') || path.endsWith('/profiles/self') ? 'GET' : 'POST');
  assert.equal(req.headers()['x-auth-transport'], 'cookie');
  assert.equal(req.headers()['x-requested-with'], 'FamilyCare');
  if (networkFailure) return route.abort();
  const challenge = { challenge_token: 'test-challenge', resend_after: resendDelay, email_status: 'queued', expires_in: 300 };
  let status = 200;
  let data = {};
  if (path.endsWith('/care-profiles') || path.endsWith('/profiles')) data = { items: [] };
  else if (path.endsWith('/profiles/self')) data = { profile: null, account: { full_name: 'Example Person', email: 'test@example.com', mobile_number: '+919876543210' } };
  else if (path.endsWith('/doctors/me')) data = { user: { id: 'doctor-id', role: 'DOCTOR' } };
  else if (path.endsWith('/patients/me')) {
    if (expireAccess) { status = 401; data = { error: { code: 'invalid_token', message: 'Token expired' } }; expireAccess = false; }
    else if (!authenticated) { status = 401; data = { error: { code: 'invalid_token', message: 'Sign in required' } }; }
    else data = { user: { id: 'patient-id', full_name: 'Example Person', role: 'PATIENT' } };
  } else if (path.endsWith('/auth/refresh')) {
    if (authenticated) data = { csrf_token: 'test-csrf', user: { role: 'PATIENT' } };
    else { status = 401; data = { error: { code: 'invalid_refresh', message: 'Sign in required' } }; }
  } else if (path.endsWith('/register')) {
    if (path.includes('/doctors/')) { status = 422; data = { error: { code: 'validation_error', message: 'Invalid request fields', fields: [{ field: 'qualification' }, { field: 'registering_council' }] } }; }
    else if (registerConflict) { status = 409; data = { error: { code: 'account_exists', message: 'Account already exists; use login or reset password' } }; }
    else { status = 202; data = challenge; }
  } else if (path.endsWith('/login')) {
    if (restricted) { status = 403; data = { error: { code: 'account_restricted', message: 'Account must be verified, approved, active and password updated' } }; }
    else if (path.includes('/patients/')) data = { csrf_token: 'test-csrf', user: { id: 'patient-id', full_name: 'Example Person', role: 'PATIENT' } };
    else data = { csrf_token: 'test-csrf', user: { id: 'doctor-id', role: 'DOCTOR' } };
  } else if (path.endsWith('/verify-email') || path.endsWith('/verify-login-otp')) {
    if (invalidOtp) { status = 400; data = { error: { code: 'invalid_otp', message: 'Invalid OTP' } }; }
    else if (path.includes('/doctors/')) { status = 202; data = { user: { role: 'DOCTOR', approval_status: 'PENDING_APPROVAL' }, message: 'Email verified. Waiting for approval.' }; }
    else data = { csrf_token: 'test-csrf', user: { id: 'patient-id', role: 'PATIENT' } };
  } else if (path.endsWith('/resend-otp')) data = { ...challenge, challenge_token: 'resent-challenge' };
  else if (path.endsWith('/request-email-verification') || path.endsWith('/forgot-password')) { status = 202; data = { ...challenge, message: 'If an eligible account exists, reset instructions are queued.' }; }
  else if (path.endsWith('/logout')) { assert.equal(req.headers()['x-csrf-token'], 'test-csrf'); authenticated = false; }
  else if (!path.endsWith('/reset-password')) throw Error('Unexpected API path: ' + path);
  if (data.csrf_token && !path.endsWith('/refresh')) authenticated = true;
  await route.fulfill({ status, json: data });
});
async function visit(path) { await page.goto(base + path); }
async function credentials() {
  await page.locator('[name=email]').fill('test@example.com');
  await page.locator('[name=password]').fill('ExamplePassword8!');
}
async function details() {
  await credentials();
  await page.locator('[name=name]').fill('Example Person');
  await page.locator('[name=phone]').fill('9876543210');
}
async function code() { await page.getByLabel('OTP digit 1', { exact: true }).fill('654321'); }
const button = name => page.getByRole('button', { name, exact: true });
try {
  for (const path of ['/customer/signup', '/customer/login', '/doctor/signup', '/doctor/login']) {
    for (const width of [375, 768, 1366]) {
      await page.setViewportSize({ width, height: 900 });
      await visit(path);
      await expect(page.locator('main h1')).toHaveCount(1);
      assert.equal(await page.locator('header').count(), 0);
      assert.equal(await page.locator('[name=confirmPassword], [name=qualification], [name=council]').count(), 0, 'No additional fields allowed');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, path + ' overflows');
    }
  }
  console.log('PASS existing auth layouts at mobile, tablet and desktop sizes');
  await visit('/customer/signup'); await details();

  await button('Send OTP').click();
  await expect(page.getByRole('heading', { name: 'Verify OTP', exact: true })).toBeVisible();
  assert.deepEqual(requests.at(-1).body, { full_name: 'Example Person', email: 'test@example.com', mobile_number: '+919876543210', password: 'ExamplePassword8!', confirm_password: 'ExamplePassword8!' });
  await expect(page.locator('.otp-resend button')).toBeDisabled();
  invalidOtp = true; await code(); await button('Verify OTP').click();
  await expect(page.getByRole('alert')).toHaveText('Invalid OTP');
  invalidOtp = false; await button('Verify OTP').click();
  await expect(page.getByRole('heading', { name: /Healthcare for Every/ })).toBeVisible();
  assert.equal(await page.evaluate(() => sessionStorage.getItem('familycare_csrf')), 'test-csrf');
  await button('Sign out').click();
  await expect(page.getByRole('heading', { name: 'Customer Login' })).toBeVisible();
  assert.equal(await page.evaluate(() => sessionStorage.getItem('familycare_csrf')), null);
  console.log('PASS registration payload, wrong OTP, cookie transport and CSRF logout');
  await visit('/customer/dashboard');
  await expect(page).toHaveURL(base + '/customer/login');
  console.log('PASS unauthenticated dashboard redirects to login');
  await visit('/doctor/signup'); await details();
  await button('Continue').click();
  await page.locator('[name=registration]').fill('DMC/1234');
  await button('Continue to OTP').click();
  await expect(page.getByRole('alert')).toContainText('Profile completion will be added');
  assert.equal('qualification' in requests.at(-1).body, false);
  assert.equal('registering_council' in requests.at(-1).body, false);
  assert.equal(requests.at(-1).body.medical_registration_number, 'DMC/1234');
  console.log('PASS original doctor fields and explicit API validation limitation');
  await visit('/customer/login'); await credentials();
  await button('Login').click();
  await expect(page.getByRole('heading', { name: /Healthcare for Every/ })).toBeVisible();
  await expect(page).toHaveURL(base + '/customer/dashboard');
  await page.getByRole('button', { name: /Child Care/ }).click();
  await expect(page.getByLabel('Child name')).toBeVisible();
  await page.getByRole('link', { name: 'Back', exact: true }).click();
  await page.getByRole('button', { name: /Women/ }).click();
  await expect(page.locator('[name=memberName]')).toBeVisible();
  await page.getByRole('link', { name: 'Back', exact: true }).click();
  await page.getByRole('button', { name: /Adult Health/ }).click();
  await expect(page.locator('[name=memberName]')).toBeVisible();
  for (const width of [375, 768, 1366]) {
    await page.setViewportSize({ width, height: 900 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'Dashboard overflows');
  }
  assert.equal(await page.getByText('Connect Ambulance').count(), 0);
  expireAccess = true;
  await page.reload();
  await expect(page).toHaveURL(base + '/customer/adult');
  await expect(page.locator('[name=memberName]')).toBeVisible();
  console.log('PASS dashboard switches, mobile layout, reload and expired-session refresh');
  assert.equal(requests.filter(request => request.path === '/api/v1/patients/verify-login-otp').length, 0, 'Login must not request OTP');
  await button('Sign out').click();
  await visit('/doctor/login'); await credentials(); await button('Login').click();
  await expect(page.getByRole('heading', { name: 'Care, with permission.' })).toBeVisible();
  assert.ok(requests.some(request => request.path === '/api/v1/doctors/login'));
  await button('Sign out').click();
  console.log('PASS patient and doctor password-only login without OTP');
  await button('Forgot Password?').click();
  await page.locator('[name=email]').fill('test@example.com');
  await button('Request Password Reset').click();
  await expect(page.getByRole('status')).toContainText('reset instructions');
  assert.equal(requests.at(-1).path, '/api/v1/auth/forgot-password');
  console.log('PASS password reset request without adding fields');
  await visit('/customer/login'); await credentials(); restricted = true;
  await button('Login').click(); await expect(page.getByRole('alert')).toContainText('Account must be verified');
  restricted = false;
  await button('Verify an unverified email').click();
  await expect(page.getByRole('heading', { name: 'Verify OTP', exact: true })).toBeVisible();
  assert.equal(requests.at(-1).path, '/api/v1/auth/request-email-verification');
  await visit('/customer/signup'); await details(); registerConflict = true;
  await button('Send OTP').click(); await expect(page.getByRole('alert')).toContainText('Account already exists');
  registerConflict = false;
  await visit('/doctor/login'); await credentials(); networkFailure = true;
  await button('Login').click(); await expect(page.getByRole('alert')).toContainText('Cannot reach the server');
  assert.deepEqual(errors, []);
  console.log('PASS restricted account recovery, registration conflict and network failure');
} finally { await browser.close(); }
