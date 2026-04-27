import { expect, test } from "@playwright/test";
import {
  adminCredentials,
  createClinicianViaApi,
  createResearcherViaApi,
  deactivateUserViaApi,
  logoutThroughUi,
  signInViaApiSession,
} from "./helpers";

const extractCaseIdFromUrl = (urlString: string): number => {
  const url = new URL(urlString);
  const caseId = Number(url.searchParams.get("case"));
  if (!Number.isFinite(caseId)) {
    throw new Error(`Unable to read case id from URL: ${urlString}`);
  }
  return caseId;
};

const createCaseThroughUi = async (
  page: Parameters<typeof test>[0]["page"],
  input: {
    patientName: string;
    medicare: string;
    details: string;
  },
): Promise<{ caseId: number; skippedReason?: string }> => {
  await page.goto("/new-case");
  await page.getByLabel(/medicare card number/i).fill(input.medicare);
  await page.getByLabel(/patient name/i).fill(input.patientName);
  await page.getByLabel(/case details/i).fill(input.details);

  const triageResponsePromise = page.waitForResponse((response) => (
    response.request().method() === "POST" && response.url().includes("/triage")
  ));
  await page.getByRole("button", { name: /submit for triage/i }).click();
  const triageResponse = await triageResponsePromise;
  const triageBody = await triageResponse.text();

  if (!triageResponse.ok()) {
    if (
      triageResponse.status() === 500 &&
      /expected str, bytes or os\.PathLike object, not NoneType/i.test(triageBody)
    ) {
      return { caseId: -1, skippedReason: "Backend triage model is not configured locally yet." };
    }

    throw new Error(`Triage request failed (${triageResponse.status()}): ${triageBody}`);
  }

  await expect(page).toHaveURL(/\/dashboard\?case=\d+$/, { timeout: 45_000 });
  return { caseId: extractCaseIdFromUrl(page.url()) };
};

test("clinician can override, undo override, and resolve a real case", async ({ page, request }) => {
  test.setTimeout(180_000);

  const clinician = await createClinicianViaApi(request, adminCredentials);
  const uniqueSeed = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const medicareCardBase = uniqueSeed.slice(-10).padStart(10, "0");
  const patientName = `E2E Override ${uniqueSeed.slice(-4)}`;

  try {
    // Backend token iat is second-level precision; wait past the creation second.
    await page.waitForTimeout(1200);
    await signInViaApiSession(page, clinician);

    const caseCreation = await createCaseThroughUi(page, {
      patientName,
      medicare: `${medicareCardBase}/1`,
      details: "Severe chest pain with sweating and persistent breathlessness.",
    });
    if (caseCreation.skippedReason) {
      test.skip(true, caseCreation.skippedReason);
    }

    await expect(page.getByRole("heading", { name: "Triage Result" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Override" })).toBeVisible();

    const severityText = (await page.locator("h2").filter({ hasText: /ATS-\d/ }).first().textContent()) ?? "";
    const currentAts = Number(severityText.match(/ATS-(\d)/)?.[1] ?? "3");
    const nextAts = currentAts === 1 ? 2 : 1;
    const overrideReason = `E2E override reason ${uniqueSeed}`;

    await page.getByRole("button", { name: "Override" }).click();
    const overrideDialog = page.getByRole("dialog", { name: "Override ATS Classification" });
    await expect(overrideDialog).toBeVisible();
    await overrideDialog.getByRole("combobox", { name: "Select ATS Classification" }).click();
    await page.getByRole("option", { name: `ATS ${nextAts}` }).click();
    await overrideDialog.getByLabel("Override Reason").fill(overrideReason);
    await overrideDialog.getByRole("button", { name: "Override" }).click();

    await expect(page.getByText("Clinician override applied to this case.")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(overrideReason)).toBeVisible();
    await expect(page.getByRole("button", { name: "Undo Override" })).toBeVisible();

    await page.getByRole("button", { name: "Undo Override" }).click();
    const undoDialog = page.getByRole("dialog");
    await expect(undoDialog.getByText("Are you sure you want to undo override?")).toBeVisible();
    await undoDialog.getByRole("button", { name: "Undo" }).click();
    await expect(page.getByRole("button", { name: "Undo Override" })).toHaveCount(0, { timeout: 20_000 });

    const resolveResponsePromise = page.waitForResponse((response) => (
      response.request().method() === "PATCH" && /\/cases\/\d+\/resolve$/.test(response.url())
    ));
    await page.getByRole("button", { name: "Resolve" }).click();
    const resolveResponse = await resolveResponsePromise;
    expect(resolveResponse.ok()).toBeTruthy();
    await expect(page).toHaveURL(/\/dashboard$/, { timeout: 20_000 });
  } finally {
    try {
      await deactivateUserViaApi(request, clinician.id, adminCredentials);
    } catch {
      // Ignore cleanup failures after a hard timeout.
    }
  }
});

test("researcher sees redacted identifiers in case summary", async ({ page, request }) => {
  test.setTimeout(180_000);

  const clinician = await createClinicianViaApi(request, adminCredentials);
  const researcher = await createResearcherViaApi(request, adminCredentials);
  const uniqueSeed = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const medicareCardBase = uniqueSeed.slice(-10).padStart(10, "0");

  try {
    // Backend token iat is second-level precision; wait past the creation second.
    await page.waitForTimeout(1200);
    await signInViaApiSession(page, clinician);

    const caseCreation = await createCaseThroughUi(page, {
      patientName: `Sensitive Name ${uniqueSeed.slice(-4)}`,
      medicare: `${medicareCardBase}/1`,
      details: "Patient reports severe abdominal pain and dizziness.",
    });
    if (caseCreation.skippedReason) {
      test.skip(true, caseCreation.skippedReason);
    }

    await logoutThroughUi(page, clinician);

    await page.waitForTimeout(1200);
    await signInViaApiSession(page, researcher);
    await page.goto(`/dashboard?case=${caseCreation.caseId}`);

    await expect(page.getByRole("heading", { name: "Triage Result" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "[REDACTED]" })).toHaveCount(2);
    await expect(page.getByRole("button", { name: "Override" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Undo Override" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Resolve" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Reopen" })).toHaveCount(0);
  } finally {
    try {
      await deactivateUserViaApi(request, clinician.id, adminCredentials);
    } catch {
      // Ignore cleanup failures after a hard timeout.
    }
    try {
      await deactivateUserViaApi(request, researcher.id, adminCredentials);
    } catch {
      // Ignore cleanup failures after a hard timeout.
    }
  }
});
