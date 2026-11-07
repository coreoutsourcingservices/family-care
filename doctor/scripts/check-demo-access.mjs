import { chromium, expect } from "@playwright/test";
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage();
const errors = [];
let sessionRequests = 0;
let delayReads = false;
page.on("pageerror", (e) => errors.push(e.message));
const profiles = [
  {
    id: "c",
    full_name: "Ama DEMO",
    module: "child",
    date_of_birth: "2018-01-01",
  },
  {
    id: "a",
    full_name: "Saif DEMO",
    module: "adult",
    date_of_birth: "1991-01-01",
  },
];
await page.route("**/api/v1/**", async (route) => {
  if (delayReads) await new Promise((resolve) => setTimeout(resolve, 1200));
  const path = new URL(route.request().url()).pathname;
  let json = { items: [], total: 0 };
  if (path.endsWith("/doctors/me")) {
    sessionRequests++;
    json = {
      user: {
        id: "doc",
        role: "DOCTOR",
        full_name: "DEMO Doctor",
        approval_status: "APPROVED",
      },
    };
  } else if (path.endsWith("/doctors/care-profiles"))
    json = { items: profiles, total: 2 };
  else if (path.endsWith("/women/shared"))
    json = {
      items: [
        {
          id: "w",
          name: "Riya DEMO",
          permissions: { records: "edit", health: "edit" },
        },
      ],
    };
  else if (path.endsWith("/adult-access/shared"))
    json = {
      items: [
        {
          id: "a",
          name: "Saif DEMO",
          permissions: { reports: "edit", bp: "edit" },
        },
      ],
    };
  else if (path.endsWith("/workspace"))
    json = {
      records: [
        {
          id: "record",
          kind: path.includes("adult-access") ? "bp" : undefined,
          section: "health",
          title: "DEMO scoped record",
          date: "2026-11-01",
          notes: "DEMO scoped notes",
          systolic: 120,
          diastolic: 80,
        },
      ],
    };
  else if (path.endsWith("/reports")) {
    if (path.includes("/doctors/care-profiles/a/"))
      return route.fulfill({
        status: 403,
        json: { error: { message: "Use scoped access" } },
      });
    json = {
      items: [
        {
          id: path,
          name: "DEMO report.pdf",
          created_at: "2026-11-05",
          category: "Lab tests",
          content_type: "application/pdf",
        },
      ],
      total: 1,
    };
  }
  return route.fulfill({ json });
});
try {
  await page.goto("http://localhost:5173/doctor/patients");
  await expect(page.locator(".dw-table")).toContainText("Riya DEMO");
  await expect(
    page.getByRole("link", { name: "View Saif DEMO" }),
  ).toHaveAttribute("href", "/doctor/adult/a");
  for (const id of ["a", "w"]) {
    await page.goto(
      "http://localhost:5173/doctor/clinical-records?patient=" + id,
    );
    await expect(page.locator(".dr-health-timeline")).toContainText(
      "DEMO scoped record",
    );
  }
  await page.goto("http://localhost:5173/doctor/reports");
  await expect(page.locator(".dr-report-main .dw-table tbody tr")).toHaveCount(
    3,
  );
  await expect(page.locator(".dr-report-main .dw-table")).toContainText(
    "Riya DEMO",
  );
  // Sidebar navigation must preserve the frame and the authenticated session gate.
  const sidebar = page.locator("aside").first();
  const frame = await sidebar.elementHandle();
  const checksBefore = sessionRequests;
  for (const route of ["patients", "clinical-records", "reports", "patients"]) {
    await page.locator(`aside a[href="/doctor/${route}"]`).first().click();
    await expect(page).toHaveURL(new RegExp(`/doctor/${route}$`));
    await expect(sidebar).toBeVisible();
    if (!(await frame.evaluate((node) => node.isConnected)))
      throw Error("Sidebar remounted during navigation");
    await expect(
      page.getByText("Opening doctor workspace...", { exact: true }),
    ).toHaveCount(0);
  }
  if (sessionRequests !== checksBefore)
    throw Error("Session reloaded during navigation");
  delayReads = true;
  await page.locator('aside a[href="/doctor/reports"]').click();
  await expect(page.locator(".dr-report-main .dw-table tbody tr")).toHaveCount(
    3,
    { timeout: 700 },
  );
  await expect(
    page.getByText("Loading your workspace...", { exact: true }),
  ).toHaveCount(0);
  await page.locator('aside a[href="/doctor/patients"]').click();
  await expect(page.locator(".dw-table")).toContainText("Riya DEMO", {
    timeout: 700,
  });
  await expect(
    page.getByText("Loading your workspace...", { exact: true }),
  ).toHaveCount(0);
  console.log(
    "PASS cached pages remain visible while slow background requests run",
  );
  console.log("PASS persistent sidebar and session across page navigation");
  if (errors.length) throw Error(errors.join("\n"));
  console.log("PASS Adult and Women scoped records, reports and patient links");
} finally {
  await browser.close();
}
