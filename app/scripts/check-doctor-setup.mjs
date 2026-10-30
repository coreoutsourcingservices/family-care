import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ reducedMotion: 'reduce' });
const base = process.env.PREVIEW_URL ?? 'http://127.0.0.1:5173';
const errors = [], calls = [];
page.on('pageerror', error => errors.push(error.message));
let scenario = 'profile', failure = 0, signup = {}, submitted = [], uploadedImages = 0;
const user = { id: 'onboarding-test-doctor', public_id: 'D000123', full_name: 'Dr Preview Doctor', email: 'doctor@example.com', phone_number: '+919876543210', role: 'DOCTOR' };
const professional = { qualification: null, specialization: null, medical_registration_number: 'REG-123', registering_council: 'DELHI MEDICAL COUNCIL', nmr_id: null, address: null, clinic_address: null, years_of_experience: null };
function setupResponse() { return { requires_profile_setup: true, setup_token: 'test-setup-token', user: { ...user, approval_status: scenario === 'rejected' ? 'REJECTED' : 'PROFILE_REQUIRED' }, doctor: { ...professional }, rejection_reason: scenario === 'rejected' ? 'Please correct your clinic address.' : null }; }
await page.route('**/api/v1/**', async route => {
  const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '');
  if (path === '/doctors/setup-images') {
    uploadedImages++;
    assert.ok(request.headers()['content-type'].startsWith('multipart/form-data'));
    return route.fulfill({ status: 201, json: { images: {} } });
  }
  const body = request.method() === 'POST' ? request.postDataJSON() : null;
  calls.push(path);
  if (path === '/doctors/register') { signup = body; return route.fulfill({ status: 202, json: { challenge_token: 'test-otp-challenge', email_status: 'sent', resend_after: 60 } }); }
  if (path === '/doctors/verify-email') return route.fulfill({ status: 202, json: scenario === 'legacy' ? { user: { ...user, approval_status: 'PENDING_APPROVAL' } } : setupResponse() });
  if (path === '/doctors/login') {
    if (scenario === 'pending') return route.fulfill({ status: 202, json: { user: { ...user, approval_status: 'PENDING_APPROVAL' }, message: 'Your profile is under review.' } });
    if (scenario === 'approved') return route.fulfill({ json: { csrf_token: 'test-csrf', user: { ...user, approval_status: 'APPROVED' } } });
    return route.fulfill({ status: 202, json: setupResponse() });
  }
  if (path === '/doctors/setup-profile') {
    submitted.push(body);
    if (failure) { const status = failure; failure = 0; return route.fulfill({ status, json: { error: { code: status === 401 ? 'invalid_token' : 'validation_error', message: status === 401 ? 'Invalid or expired token' : 'Please review your clinic address' } } }); }
    return route.fulfill({ status: 202, json: { user: { ...user, approval_status: 'PENDING_APPROVAL' }, message: 'Your profile is under review.' } });
  }
  if (path === '/doctors/me') return scenario === 'approved' ? route.fulfill({ json: { user: { ...user, approval_status: 'APPROVED' } } }) : route.fulfill({ status: 401, json: { error: { code: 'session_required', message: 'Please sign in again' } } });
  if (path === '/doctors/referral') return route.fulfill({ json: { doctor: { referral_id: 'previewD000123' } } });
  if (path.startsWith('/doctors/')) return route.fulfill({ json: { items: [], total: 0 } });
  return route.fulfill({ status: 404, json: { error: { code: 'not_found', message: 'Not part of this test' } } });
});
async function login() {
  await page.goto(base + '/doctor/login');
  await page.locator('input[name=email]').fill(user.email);
  await page.locator('input[name=password]').fill('ExamplePassword8!');
  await page.getByRole('button', { name: 'Login', exact: true }).click();
}
async function fillSetup() {
  await page.locator('input[name=qualification]').fill('MBBS');
  await page.locator('textarea[name=address]').fill('12 Example Road, Delhi 110001');
  await page.locator('textarea[name=clinic_address]').fill('21 Example Clinic, Delhi 110002');
  await page.locator('input[name=years_of_experience]').fill('0');
}
await mkdir('app/.preview', { recursive: true });
try {
  for (const width of [390, 1366, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    scenario = 'profile'; submitted = [];
    await page.goto(base + '/doctor/signup');
    await page.locator('input[name=name]').fill(user.full_name);
    await page.locator('input[name=phone]').fill('9876543210');
    await page.locator('input[name=email]').fill(user.email);
    await page.locator('input[name=password]').fill('ExamplePassword8!');
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    assert.equal(await page.locator('input[name=specialization],input[name=nmr]').count(), 0);
    await page.locator('input[name=qualification]').fill('MBBS');
    await page.locator('input[name=registration]').fill('REG-123');
    await page.locator('select[name=council]').selectOption('Delhi Medical Council');
    await page.getByRole('button', { name: 'Continue to OTP', exact: true }).click();
    await page.getByRole('heading', { name: 'Verify OTP', exact: true }).waitFor();
    assert.deepEqual(Object.keys(signup).sort(), ['full_name', 'email', 'mobile_number', 'password', 'confirm_password', 'medical_registration_number', 'registering_council', 'qualification'].sort());
    assert.equal(signup.qualification, 'MBBS');
    await page.getByLabel('OTP digit 1', { exact: true }).fill('123456');
    await page.getByRole('button', { name: 'Verify OTP', exact: true }).click();
    await expect(page).toHaveURL(base + '/doctor/dashboard');
    await expect(page.getByRole('heading', { name: 'Set My Profile', exact: true })).toBeVisible();
    assert.equal(calls.includes('/doctors/care-profiles'), false);
    for (const label of ['Patients', 'Consultations', 'Clinical Records', 'Appointments', 'Prescriptions', 'Reports', 'Settings']) {
      const button = page.getByRole('navigation', { name: 'Doctor workspace' }).getByRole('button', { name: label, exact: true });
      await expect(button).toBeDisabled();
      await button.evaluate(element => element.click());
      await expect(page).toHaveURL(base + '/doctor/dashboard');
    }
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.equal(await page.locator('.doctor-home-sidebar img').count(), 0, 'Sidebar must not include decorative pictures');
    assert.equal(submitted.length, 0, 'Opening the basic dashboard must not request approval');
    await page.screenshot({ path: `app/.preview/doctor-home-${width}.png`, fullPage: true });
    await page.getByRole('link', { name: 'Set My Profile', exact: true }).last().click();
    await expect(page).toHaveURL(base + '/doctor/setup-account');
    await expect(page.getByRole('heading', { name: 'Your verified account', exact: true })).toBeVisible();
    assert.equal(submitted.length, 0, 'OTP must not submit an approval request');
    for (const name of ['verified_name', 'verified_email', 'verified_phone']) assert.equal(await page.locator(`input[name=${name}]`).getAttribute('readonly'), '');
    assert.equal(await page.locator('input[name=medical_registration_number]').inputValue(), 'REG-123');
    assert.equal(await page.locator('select[name=registering_council]').inputValue(), 'Delhi Medical Council');
    assert.equal(await page.locator('input[type=file]').count(), 2);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.equal(await page.evaluate(() => location.href.includes('test-setup-token') || JSON.stringify({ ...localStorage, ...sessionStorage }).includes('test-setup-token')), false, 'Setup token leaked into persistent storage or URL');
    await page.getByRole('button', { name: 'Proceed for Approval', exact: true }).click();
    assert.equal(submitted.length, 0, 'Missing qualification/address must block submission');
    await fillSetup();
    await page.locator('input[name=medical_registration_number]').fill('!bad');
    assert.equal(await page.locator('input[name=medical_registration_number]').evaluate(input => input.checkValidity()), false);
    await page.locator('input[name=medical_registration_number]').fill('REG-123');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: `app/.preview/doctor-setup-${width}.png`, fullPage: true });
    if (width === 390) {
      const image = { name: 'doctor.png', mimeType: 'image/png', buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a/5kAAAAASUVORK5CYII=', 'base64') };
      await page.locator('input[name=profile_photo]').setInputFiles(image);
      await page.locator('input[name=degree_photo]').setInputFiles(image);
      assert.equal(uploadedImages, 0, 'Selecting photos must not upload or request approval');
      failure = 422;
      await page.getByRole('button', { name: 'Proceed for Approval', exact: true }).click();
      await expect(page.getByRole('alert')).toContainText('clinic address');
      assert.equal(await page.locator('input[name=qualification]').inputValue(), 'MBBS');
      assert.equal(uploadedImages, 2, 'Both images must upload before submission');
    }
    await page.getByRole('button', { name: 'Proceed for Approval', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Your profile is under review.', exact: true })).toBeVisible();
    if (width === 390) assert.equal(uploadedImages, 2, 'Retry must not upload saved images again');
    const payload = submitted.at(-1);
    assert.equal(payload.setup_token, 'test-setup-token');
    assert.equal(payload.years_of_experience, 0);
    assert.equal(payload.specialization, null);
    assert.equal(payload.nmr_id, null);
    assert.equal('email' in payload || 'password' in payload || 'full_name' in payload, false);
    assert.equal(page.url().includes('/dashboard'), true);
    console.log(`PASS signup -> OTP -> account setup -> approval at ${width}px`);
  }
  scenario = 'legacy';
  await page.goto(base + '/doctor/signup');
  for (const [name, value] of Object.entries({ name: user.full_name, phone: '9876543210', email: user.email, password: 'ExamplePassword8!' })) await page.locator(`input[name=${name}]`).fill(value);
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await page.locator('input[name=qualification]').fill('MBBS');
  await page.locator('input[name=registration]').fill('REG-123');
  await page.locator('select[name=council]').selectOption('Delhi Medical Council');
  await page.getByRole('button', { name: 'Continue to OTP', exact: true }).click();
  await page.getByLabel('OTP digit 1', { exact: true }).fill('123456');
  await page.getByRole('button', { name: 'Verify OTP', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('backend skipped Account Setup');
  assert.equal(await page.getByRole('heading', { name: 'Your profile is under review.', exact: true }).count(), 0);
  scenario = 'profile';
  await login(); await expect(page).toHaveURL(base + '/doctor/dashboard');
  await page.getByRole('link', { name: 'Set My Profile', exact: true }).last().click();
  await expect(page).toHaveURL(base + '/doctor/setup-account');
  await page.reload(); await expect(page).toHaveURL(base + '/doctor/login');
  scenario = 'rejected';
  Object.assign(professional, { qualification: 'MD', address: 'Old Personal Address', clinic_address: 'Old Clinic Address', years_of_experience: 5, registering_council: 'Example Other Council' });
  await login(); await expect(page).toHaveURL(base + '/doctor/dashboard');
  await page.getByRole('link', { name: 'Set My Profile', exact: true }).last().click();
  await expect(page).toHaveURL(base + '/doctor/setup-account');
  await expect(page.locator('.doctor-setup-rejection')).toContainText('Please correct your clinic address.');
  assert.equal(await page.locator('input[name=qualification]').inputValue(), 'MD');
  assert.equal(await page.locator('input[name=other_council]').inputValue(), 'Example Other Council');
  assert.equal(await page.locator('input[name=years_of_experience]').inputValue(), '5');
  await page.locator('textarea[name=clinic_address]').fill('Corrected Clinic Address, Delhi');
  await page.getByRole('button', { name: 'Proceed for Approval', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Your profile is under review.', exact: true })).toBeVisible();
  scenario = 'pending';
  await login(); await expect(page.getByRole('heading', { name: 'Your profile is under review.', exact: true })).toBeVisible();
  assert.equal(page.url().includes('/dashboard'), true);
  scenario = 'profile';
  await login(); await expect(page).toHaveURL(base + '/doctor/dashboard');
  await page.getByRole('link', { name: 'Set My Profile', exact: true }).last().click();
  await expect(page).toHaveURL(base + '/doctor/setup-account');
  failure = 401;
  await page.getByRole('button', { name: 'Proceed for Approval', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Your setup session has expired.', exact: true })).toBeVisible();
  assert.equal(calls.includes('/auth/refresh'), false, 'Setup failures must not refresh a dashboard session');
  scenario = 'approved';
  await login(); await expect(page).toHaveURL(base + '/doctor/dashboard');
  assert.equal(errors.length, 0, errors.join('\n'));
  console.log('PASS read-only identity, required fields, retry, zero experience, private setup token, refresh/login recovery, rejected-profile resubmission, pending/approved gating and expired token. Mock APIs only; no emails or real applications sent.');
} finally { await browser.close(); }
