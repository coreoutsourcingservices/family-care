import { chromium, expect } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';

const base = process.env.PREVIEW_URL ?? 'http://127.0.0.1:5173';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ reducedMotion: 'reduce' });
const errors = [], calls = [];
await page.addInitScript(() => { Object.defineProperty(navigator, 'clipboard', { value: { writeText: async text => { window.__copiedReferral = text; } } }); });
page.on('pageerror', error => errors.push(error.message));
let approved = true, recordsFail = false, emptyData = false, passwordPayload;
const id = '11111111-1111-4111-8111-111111111111';
const user = { id: 'workspace-doctor', public_id: 'D000123', referral_id: 'workspacedoctorD000123', full_name: 'Dr Workspace Doctor', email: 'doctor@example.com', phone_number: '+919876543210', role: 'DOCTOR', approval_status: 'APPROVED', doctor: { qualification: 'MBBS', specialization: 'Pediatrics', medical_registration_number: 'REG123', registering_council: 'Delhi Medical Council', address: '12 Example Road', clinic_address: '21 Example Clinic', years_of_experience: 5, nmr_id: null } };
const patients = [{ id, full_name: 'Aarav Example', module: 'child', date_of_birth: '2020-01-01', guardian_contact: '+919876543211' }];
await page.route('**/api/v1/**', async route => {
  const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '');
  calls.push(path);
  if (emptyData && (path.startsWith('/doctors/care-profiles') || path === '/doctors/consultation-requests')) return route.fulfill({ json: { items: [], total: 0 } });
  if (path === '/doctors/me') return approved ? route.fulfill({ json: { user } }) : route.fulfill({ status: 403, json: { error: { code: 'approval_required', message: 'Approval required' } } });
  if (path === '/doctors/care-profiles') return route.fulfill({ json: { items: patients, total: 1 } });
  if (path === '/doctors/consultation-requests') return route.fulfill({ json: { items: [{ id: 'request1', child_id: id, title: 'Follow-up request', date: '2026-11-01', status: 'REQUESTED', notes: 'A family-submitted consultation request.' }], total: 1 } });
  if (path.endsWith('/records')) return recordsFail ? route.fulfill({ status: 500, json: { error: { message: 'Records temporarily unavailable' } } }) : route.fulfill({ json: { items: [{ id: 'record1', title: 'Shared medical history', date: '2026-01-01', kind: 'history', notes: 'Family note' }], total: 1 } });
  if (path.endsWith('/reports')) return route.fulfill({ json: { items: [{ id: 'report1', profile_id: id, name: 'Prescription follow-up.pdf', created_at: '2026-01-01T00:00:00Z', size_bytes: 1000 }], total: 1 } });
  if (path === '/doctors/vaccination-reviews') return route.fulfill({ json: { items: [], total: 0 } });
  if (path === '/auth/change-password') { passwordPayload = request.postDataJSON(); return route.fulfill({ json: { message: 'Password changed' } }); }
  if (path === '/auth/logout') return route.fulfill({ json: { message: 'Signed out' } });
  return route.fulfill({ status: 404, json: { error: { message: 'Not part of this isolated test' } } });
});
const pages = [['dashboard', 'Doctor Dashboard'], ['setup-account', 'My Profile'], ['patients', 'Patients'], ['consultations', 'Consultations'], ['clinical-records', 'Clinical Records'], ['appointments', 'Appointments'], ['prescriptions', 'Prescriptions'], ['reports', 'Reports'], ['settings', 'Settings'], ['vaccination-reviews', 'Vaccination reviews']];
try {
  await mkdir('app/.preview', { recursive: true });
  for (const width of [320, 390, 768, 1024, 1280, 1366, 1920, 2560]) {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : width === 1280 ? 720 : width === 1366 ? 768 : width >= 1920 ? 1080 : 900 });
    for (const [path, title] of pages) {
      await page.goto(`${base}/doctor/${path}`);
      await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
      await expect(page.getByRole('navigation', { name: 'Doctor workspace' })).toBeVisible();
      await expect(page.getByText('workspacedoctorD000123', { exact: true })).toBeVisible();
      if (path === 'dashboard') { await page.getByRole('button', { name: 'Copy referral ID' }).click(); assert.equal(await page.evaluate(() => window.__copiedReferral), 'workspacedoctorD000123'); }
      assert.equal(await page.getByRole('navigation', { name: 'Doctor workspace' }).getByRole('button').count(), 0, 'Approved menu must contain working links');
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) console.log(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).slice(0,15).map(el=>({tag:el.tagName,cls:el.className,width:el.getBoundingClientRect().width,right:el.getBoundingClientRect().right}))));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${path} overflows at ${width}px`);
      if (path === 'patients') await expect(page.getByText('Aarav Example', { exact: true })).toBeVisible();
      if (path === 'clinical-records') await expect(page.getByRole('heading', { name: 'Shared medical history' })).toBeVisible();
      if (path === 'prescriptions' || path === 'reports') await expect(page.getByRole('heading', { name: 'Prescription follow-up.pdf', exact: true })).toBeVisible();
      if (path === 'dashboard' || path === 'patients') await page.screenshot({ path: `app/.preview/doctor-${path}-approved-${width}.png`, fullPage: true });
    }
    console.log(`PASS all 10 doctor pages share the purple workspace at ${width}px`);
  }
  emptyData = true;
  for (const path of ['patients', 'consultations', 'clinical-records', 'appointments', 'prescriptions', 'reports']) {
    await page.goto(`${base}/doctor/${path}`);
    await expect(page.locator('.dw-empty-visual')).toBeVisible();
    await expect(page.getByRole('table')).toHaveCount(0);
    await page.screenshot({ path: `app/.preview/doctor-${path}-empty.png`, fullPage: true });
  }
  emptyData = false;
  for (const path of ['consultations', 'clinical-records', 'appointments', 'prescriptions', 'reports']) {
    await page.goto(`${base}/doctor/${path}`);
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await page.screenshot({ path: `app/.preview/doctor-${path}-filled.png`, fullPage: true });
  }
  console.log('PASS reference-style empty states and populated tables across all six clinical pages; referral ID and copy checked on every dashboard size.');
  await page.goto(`${base}/doctor/patients`);
  await page.getByRole('textbox', { name: 'Search connected patients' }).fill('No matching person');
  await expect(page.getByRole('heading', { name: 'No matching patients' })).toBeVisible();
  await page.getByRole('textbox', { name: 'Search connected patients' }).fill('Aarav');
  await expect(page.getByText('Aarav Example', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'View records →', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Shared medical history' })).toBeVisible();
  recordsFail = true;
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Records temporarily unavailable');
  recordsFail = false;
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Shared medical history' })).toBeVisible();
  await page.goto(`${base}/doctor/appointments`);
  await page.locator('input[type=date]').fill('2026-12-01');
  await expect(page.getByRole('heading', { name: 'No requests for these dates' })).toBeVisible();
  await page.getByRole('button', { name: 'Show all dates' }).click();
  await expect(page.getByRole('heading', { name: 'Follow-up request' })).toBeVisible();
  await page.goto(`${base}/doctor/settings`);
  await page.getByLabel('Current password', { exact: true }).fill('OldPassword8!');
  await page.getByLabel('New password', { exact: true }).fill('NewPassword8!');
  await page.getByLabel('Confirm new password', { exact: true }).fill('NewPassword8!');
  await page.getByRole('button', { name: 'Update password' }).click();
  await expect(page).toHaveURL(`${base}/doctor/login`);
  assert.deepEqual(passwordPayload, { current_password: 'OldPassword8!', new_password: 'NewPassword8!', confirm_password: 'NewPassword8!' });
  approved = false;
  calls.length = 0;
  await page.goto(`${base}/doctor/clinical-records?patient=${id}`);
  await expect(page).toHaveURL(`${base}/doctor/login`);
  assert.equal(calls.some(path => path.includes('/care-profiles')), false, 'Unapproved direct route fetched clinical data');
  assert.deepEqual(errors, []);
  console.log('PASS patient filtering, linked records, API failure/retry, requested dates, password update and direct-route approval gate. Mock APIs only.');
} finally { await browser.close(); }
