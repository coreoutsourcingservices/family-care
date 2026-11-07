import { chromium, expect } from "@playwright/test";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const user = {
  id: "doctor",
  role: "DOCTOR",
  full_name: "Dr. Carter",
  public_id: "D000123",
  referral_id: "carterD000123",
  approval_status: "APPROVED",
  email: "doctor@example.invalid",
  doctor: { qualification: "MBBS", specialization: "Family Medicine" },
};
const patients = [
  {
    id: "patient1",
    full_name: "Aarav Sharma",
    module: "child",
    date_of_birth: "2018-06-15",
    created_at: "2026-01-01",
  },
  {
    id: "patient2",
    full_name: "Neha Verma",
    module: "women",
    date_of_birth: "1998-01-01",
    created_at: "2026-02-01",
  },
  {
    id: "patient3",
    full_name: "Rohit Singh",
    module: "adult",
    date_of_birth: "1991-01-01",
    created_at: "2026-02-01",
  },
];
const today = new Date().toISOString();
let schedule = {
  version: 1,
  windows: [
    {
      id: "11111111-1111-4111-8111-111111111111",
      start: "10:00",
      end: "12:00",
      capacity: 20,
      days: [0, 1, 2, 3, 4, 5, 6],
    },
  ],
};
let savedSchedule;

await page.route("**/api/v1/**", (route) => {
  const path = new URL(route.request().url()).pathname;
  let data = { items: [], total: 0 };
  if (path.endsWith("/appointment-schedule")) {
    if (route.request().method() === "PUT") {
      savedSchedule = route.request().postDataJSON();
      schedule = { ...savedSchedule, version: schedule.version + 1 };
    }
    return route.fulfill({ json: schedule });
  }
  if (path.endsWith("/prescriptions"))
    return route.fulfill({
      json: {
        items: [
          {
            id: "rx1",
            status: "DRAFT",
            version: 1,
            doctor_name: "Dr. Carter",
            issued_at: null,
            data: {
              medicines: [
                {
                  name: "DEMO medicine",
                  strength: "Sample",
                  dose: "Sample",
                  frequency: "Sample",
                  duration: "Sample",
                  instructions: "Synthetic test fixture only",
                },
              ],
              instructions: "DEMO fixture",
              follow_up: null,
            },
          },
        ],
      },
    });
  if (path.endsWith("/doctors/me")) data = { user };
  else if (path.endsWith("/doctors/care-profiles"))
    data = { items: patients, total: 3 };
  else if (path.endsWith("/consultation-requests"))
    data = {
      items: [
        {
          id: "request1",
          child_id: "patient1",
          title: "Follow-up",
          date: today.slice(0, 10),
          status: "REQUESTED",
          notes: "Shared symptom notes",
          pulse: 82,
        },
      ],
      total: 1,
    };
  else if (path.endsWith("/consultation-visits"))
    data = {
      items: [
        {
          id: "visit1",
          patient_name: "Aarav Sharma",
          concern: "Follow-up",
          status: "CONFIRMED",
          requested_at: today,
          confirmed_at: today,
          duration_minutes: 30,
          version: 1,
        },
      ],
      total: 1,
    };
  else if (path.endsWith("/records"))
    data = {
      items: [
        {
          id: "record1",
          title: "Shared medical history",
          date: "2026-10-20",
          kind: "history",
          notes: "Family-reported history",
          source_role: "PATIENT",
        },
      ],
      total: 1,
    };
  else if (path.endsWith("/reports"))
    data = {
      items: [
        {
          id: "report-" + path.split("/")[5],
          profile_id: "patient1",
          name: "CBC Report.pdf",
          category: "Lab tests",
          content_type: "application/pdf",
          created_at: today,
        },
      ],
      total: 1,
    };
  return route.fulfill({ json: data });
});
try {
  await mkdir("app/.preview", { recursive: true });
  for (const width of [1440, 1366, 390, 320, 255]) {
    await page.setViewportSize({ width, height: 940 });
    for (const path of [
      "dashboard",
      "patients",
      "consultations",
      "appointments",
      "clinical-records",
      "reports",
      "prescriptions",
      "subscription",
    ]) {
      await page.goto("http://localhost:5173/doctor/" + path);
      await expect(page.locator(".doctor-workspace")).toBeVisible();
      await expect(page.locator(".doctor-referral-disclosure")).toHaveCount(0);
      await expect(page.getByRole("button", { name: /^Refresh/i })).toHaveCount(
        0,
      );
      const header = await page.locator(".doctor-home-header").boundingBox();
      const content = await page
        .locator(".doctor-workspace-content")
        .boundingBox();
      assert.ok(
        content.y >= header.y + header.height - 1,
        "Header must not overlap page content",
      );
      if (width <= 760) {
        await page
          .getByRole("button", { name: "Open navigation", exact: true })
          .click();
        await expect(
          page.getByRole("navigation", { name: "Doctor workspace" }),
        ).toBeVisible();
        await page
          .getByRole("button", { name: "Close navigation", exact: true })
          .click();
      }
      if (path === "dashboard") {
        await expect(page.locator(".dr-patient-donut strong")).toHaveText("3");
        await expect(page.locator(".dr-today")).toContainText("Aarav Sharma");
        await page
          .getByRole("combobox", { name: "Clinical activity date range" })
          .selectOption("30");
        await expect(page.locator(".dr-clinical canvas")).toHaveAttribute(
          "aria-label",
          /Consultation activity/,
        );
        await expect(page.locator(".dr-quick a")).toHaveCount(4);
        await expect(page.locator(".doctor-slot-card")).toHaveCount(0);
        await expect(
          page
            .getByRole("navigation", { name: "Doctor workspace" })
            .getByRole("link", { name: "Vaccination", exact: true }),
        ).toHaveCount(0);
      }
      if (path === "subscription") {
        await expect(
          page.getByRole("heading", { name: "Subscription", exact: true }),
        ).toBeVisible();
        await expect(page.locator(".dr-subscription-hero")).toContainText(
          "Dr. Carter",
        );
        const navNames = await page
          .getByRole("navigation", { name: "Doctor workspace" })
          .getByRole("link")
          .allTextContents();
        assert.equal(navNames.at(-1), "Subscription");
        assert.equal(navNames.at(-2), "Settings");
      }
      if (path === "patients") {
        await expect(
          page.getByText("Additional shared workspace access"),
        ).toHaveCount(0);
        await page
          .getByRole("button", { name: "Adult Health (1)", exact: true })
          .click();
        await expect(page.locator(".dw-table")).toContainText("Rohit Singh");
        await expect(page.locator(".dw-table")).not.toContainText(
          "Aarav Sharma",
        );
      }
      if (path === "consultations") {
        await expect(page.locator(".dr-visit-management")).toHaveCount(0);
        await expect(page.locator(".dr-consultation-detail")).toContainText(
          "Shared symptom notes",
        );
        await page
          .getByRole("button", { name: "History", exact: true })
          .click();
        await expect(page.locator(".dr-consultation-detail")).toContainText(
          "Shared medical history",
        );
      }
      if (path === "prescriptions") {
        await page
          .getByRole("combobox", { name: "Select prescription patient" })
          .selectOption("patient1");
        await expect(page.locator(".dr-bento-grid canvas")).toHaveCount(2);
        await expect(page.locator(".dr-rx-detail")).toContainText(
          "DEMO medicine",
        );
        await page
          .getByRole("button", { name: "+ New Prescription", exact: true })
          .click();
        await expect(page.locator(".prescription-editor")).toBeVisible();
        await page.getByRole("button", { name: "Cancel", exact: true }).click();
      }
      if (path === "appointments") {
        await page
          .getByRole("button", { name: "Manage Slots", exact: true })
          .click();
        await expect(
          page.getByRole("dialog", { name: "Manage custom appointment slots" }),
        ).toBeVisible();
        await page.getByLabel("Start time 1", { exact: true }).fill("08:17");
        await page.getByLabel("End time 1", { exact: true }).fill("10:42");
        await page
          .getByRole("spinbutton", { name: "Patient capacity 1", exact: true })
          .fill("50");
        await page
          .getByRole("button", {
            name: "Save appointment schedule",
            exact: true,
          })
          .click();
        await expect(
          page.getByText("Appointment schedule saved.", { exact: false }),
        ).toBeVisible();
        assert.equal(savedSchedule.windows[0].capacity, 50);
        assert.equal(savedSchedule.windows[0].end, "10:42");
        await page
          .getByRole("button", { name: "Close slot settings", exact: true })
          .click();
        await expect(page.locator(".dr-calendar")).toBeVisible();
        await page.locator(".dr-calendar-days button").first().click();
        await expect(page.locator(".dr-calendar-days .active")).toHaveCount(1);
      }
      if (path === "clinical-records")
        await expect(page.locator(".dr-bento-grid canvas")).toHaveCount(2);
      if (path === "clinical-records")
        await expect(page.locator(".dr-health-timeline")).toContainText(
          "Shared medical history",
        );
      if (path === "reports")
        await expect(page.locator(".dr-report-stats")).toContainText(
          "Lab Reports",
        );
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        `${path} overflow at ${width}`,
      );
      if (width <= 760) {
        for (const box of await page
          .locator(
            ".doctor-workspace-content .dw-panel,.doctor-workspace-content .ap-panel",
          )
          .all()) {
          if (await box.isVisible()) {
            const b = await box.boundingBox();
            assert.ok(
              b.x >= -1 && b.x + b.width <= width + 1,
              `${path}: panel clipped at ${width}px`,
            );
          }
        }
      }
      if (width === 1440 || width === 390 || width === 255)
        await page.screenshot({
          path: `app/.preview/doctor-redesign-${path}-${width}.png`,
          fullPage: true,
        });
    }
    console.log(
      "PASS doctor redesign pages and interactions at " + width + "px",
    );
  }
  await page.goto("http://localhost:5173/doctor/reports?patient=patient1");
  await page
    .getByRole("textbox", { name: "Search patients and records" })
    .fill("missing-report");
  await page
    .getByRole("textbox", { name: "Search patients and records" })
    .press("Enter");
  await expect(page).toHaveURL(/patient=patient1.*search=missing-report/);
  await expect(
    page.getByRole("heading", { name: "No matching reports" }),
  ).toBeVisible();
  await page.goto("http://localhost:5173/doctor/patients");
  await expect(page.locator("#doctor-referral-id")).toHaveCount(0);
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
