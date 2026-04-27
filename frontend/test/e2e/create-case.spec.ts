import { expect, test } from "@playwright/test";
import {
  adminCredentials,
  createClinicianViaApi,
  deactivateUserViaApi,
  signInViaApiSession,
} from "./helpers";

test("a clinician created from real backend can submit a case end-to-end", async ({ page, request }) => {
  test.setTimeout(120_000);

  const clinician = await createClinicianViaApi(request, adminCredentials);
  const uniqueSeed = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const medicareCardBase = uniqueSeed.slice(-10).padStart(10, "0");
  const patientName = `E2E Patient ${uniqueSeed.slice(-4)}`;

  try {
    // Backend token iat is second-level precision; wait past the creation second.
    await page.waitForTimeout(1200);
    await signInViaApiSession(page, clinician);
    await page.goto("/new-case");

    await page.getByLabel(/medicare card number/i).fill(`${medicareCardBase}/1`);
    await page.getByLabel(/patient name/i).fill(patientName);
    await page.getByLabel(/case details/i).fill("Severe chest pain with shortness of breath.");

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
        test.skip(true, "Backend triage model is not configured locally yet.");
      }

      throw new Error(
        `Triage request failed (${triageResponse.status()}): ${triageBody}`
      );
    }

    await expect(page).toHaveURL(/\/dashboard\?case=\d+$/, { timeout: 45_000 });
    await expect(page.getByRole("heading", { name: "Triage Result" })).toBeVisible({ timeout: 45_000 });
    await expect(page.getByText(patientName)).toBeVisible();
  } finally {
    try {
      await deactivateUserViaApi(request, clinician.id, adminCredentials);
    } catch {
      // Ignore cleanup failures after a hard timeout.
    }
  }
});
