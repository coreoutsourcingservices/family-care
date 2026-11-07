import { chromium, expect } from "@playwright/test";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let legacyAvailability = false;
let module = "adult",
  bookings = [],
  saved = [],
  uploads = 0;
const doctor = {
  id: "doc",
  name: "Dr Sample",
  specialization: "Family medicine",
  qualification: "MBBS",
  experience: 8,
  referral_id: "sampleD000007",
  rating: null,
  review_count: 0,
};
const options = {
  physical_enabled: true,
  video_enabled: false,
  physical_fee_paise: 55000,
  video_fee_paise: null,
};
await page.route("**/api/v1/**", (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname;
  const json = (data) => route.fulfill({ json: data });
  const profile = {
    id: "profile-" + module,
    profile_type: "self",
    module,
    full_name: "QA " + module,
    date_of_birth: module === "child" ? "2020-01-01" : "1995-01-01",
    created_at: "2026-01-01",
    family_access: true,
  };
  if (path.endsWith("/patients/me"))
    return json({
      user: { id: "owner", role: "PATIENT", full_name: "QA Owner" },
    });
  if (path === "/api/v1/patients/profiles")
    return json({ items: [profile], total: 1 });
  if (path === "/api/v1/patients/profiles/" + profile.id)
    return json({ profile });
  if (path.endsWith("/doctor-directory"))
    return json({ items: [doctor], total: 1 });
  if (path.endsWith("/appointment-availability"))
    return json({
      items: [
        {
          id: "slot",
          start: "10:00",
          end: "12:00",
          status: "AVAILABLE",
          remaining: 4,
        },
        {
          id: "full",
          start: "14:00",
          end: "16:00",
          status: "FULL",
          remaining: 0,
        },
      ],
      doctor: {
        ...doctor,
        clinic_address: "Sample clinic, Main Road",
        ...(legacyAvailability ? {} : {consultation_options: options}),
      },
    });
  if (path.endsWith("/appointments") && req.method() === "POST") {
    const value = req.postDataJSON();
    saved.push(value);
    const appointment = {
      ...value,
      id: "booking-" + module,
      doctor_name: doctor.name,
      start: "10:00",
      end: "12:00",
      status: "BOOKED",
      details: { mode: value.mode, notes: value.notes, fee_paise: 55000 },
    };
    bookings.push(appointment);
    return json({ appointment });
  }
  if (path.endsWith("/appointments")) return json({ items: bookings });
  if (path.endsWith("/reports") && req.method() === "POST") {
    uploads++;
    return json({ report: { id: "report-" + uploads } });
  }
  if (path.endsWith("/workspace"))
    return json({
      profile: {
        id: profile.id,
        name: profile.full_name,
        dob: profile.date_of_birth,
      },
      owner: true,
      permissions: {},
      records: [],
    });
  if (path.endsWith("/dashboard"))
    return json({
      child: { age: { display: "6 years" } },
      counts: {},
      vaccination: { status: "NOT_AVAILABLE" },
    });
  if (path.endsWith("/age")) return json({ age: { display: "6 years" } });
  if (path.endsWith("/pregnancy-care"))
    return json({ settings: null, guide: null });
  return json({
    items: [],
    total: 0,
    unread_count: 0,
    status: "NOT_AVAILABLE",
  });
});
try {
  await mkdir("app/.preview", { recursive: true });
  for (module of ["adult", "women", "child"]) {
    bookings = [];
    await page.goto(
      "http://localhost:5173/customer/" +
        module +
        "/" +
        (module === "adult" ? "consultation_request" : "consultation"),
    );
    await page
      .getByRole("button", { name: "Request consultation", exact: true })
      .first()
      .click();
    await expect(
      page.getByRole("heading", { name: "Book a consultation", exact: true }),
    ).toBeVisible();
    await expect(page.locator(".cb-doctor")).toContainText("550");
    await expect(
      page.getByRole("button", { name: /Video consultation/ }),
    ).toHaveCount(0);
    await expect(page.locator(".cb-slots button").nth(1)).toBeDisabled();
    await page.locator(".cb-slots button").first().click();
    await page.getByLabel("Notes for the doctor").fill("QA consultation notes");
    await page
      .locator(".cb-upload input")
      .setInputFiles({
        name: "sample.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 synthetic"),
      });
    await page.setViewportSize({ width: 390, height: 844 });
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      "Mobile overflow " + module,
    );
    if(module === "adult") { const profileBox = await page.getByRole("combobox",{name:"Switch adult profile"}).boundingBox(); assert(profileBox.width >= 90, "Profile name must remain readable on mobile"); }
    await page.screenshot({
      path: "app/.preview/booking-" + module + "-390.png",
      fullPage: true,
    });
    await page.setViewportSize({ width: 1366, height: 900 });
    await page
      .getByRole("button", { name: "Book in-person consultation", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Appointment booked", exact: true }),
    ).toBeVisible();
    assert.equal(saved.at(-1).notes, "QA consultation notes");
    assert.equal(saved.at(-1).mode, "physical");
    assert.equal(saved.at(-1).expected_fee_paise, 55000);
    assert.equal(saved.at(-1).report_ids.length, 1);
    console.log(
      "PASS " +
        module +
        " booking, fee, hidden video mode, full slot, upload, notes and mobile fit",
    );
  }
  legacyAvailability = true;
  module = "adult";
  await page.goto("http://localhost:5173/customer/adult/consultation_request");
  await page.getByRole("button",{name:"Request consultation",exact:true}).first().click();
  await expect(page.locator('.cb-slots button')).toHaveCount(2);
  await expect(page.getByText('The doctor needs to set a fee before this mode can be booked.')).toBeVisible();
  const calendar = await page.locator('.cb-calendar').boundingBox();
  assert(calendar.width <= 281, 'Calendar should stay compact');
  console.log('PASS legacy availability without fee fields does not crash, and compact calendar');
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
