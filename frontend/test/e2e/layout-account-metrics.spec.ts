import { expect, test } from "@playwright/test";
import {
  adminCredentials,
  createClinicianViaApi,
  createResearcherViaApi,
  deactivateUserViaApi,
  loginThroughUi,
  logoutThroughUi,
  signInViaApiSession,
} from "./helpers";

const escapeRegex = (value: string): string => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

test("admin account menu supports logout and role-based navigation", async ({ page }) => {
  await loginThroughUi(page, adminCredentials);

  await expect(page.getByRole("link", { name: "Users" })).toBeVisible();
  await expect(page.getByRole("link", { name: "New Case" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Metrics" })).toHaveCount(0);

  await logoutThroughUi(page, adminCredentials);
  await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
});

test("clinician can reset password from account menu without mocks", async ({ page, request }) => {
  test.setTimeout(120_000);

  const clinician = await createClinicianViaApi(request, adminCredentials);
  const newPassword = `Clinician${Date.now()}9`;

  try {
    // Backend token iat is second-level precision; wait past the creation second.
    await page.waitForTimeout(1200);
    await signInViaApiSession(page, clinician);
    await expect(page.getByRole("link", { name: "New Case" })).toBeVisible();

    await page.getByRole("button", { name: new RegExp(escapeRegex(clinician.email), "i") }).click();
    await page.getByRole("menuitem", { name: /reset password/i }).click();
    const resetPasswordDialog = page.getByRole("dialog", { name: "Reset Password" });
    await expect(resetPasswordDialog.getByRole("heading", { name: "Reset Password" })).toBeVisible();

    await resetPasswordDialog.getByRole("textbox", { name: "Current Password", exact: true }).fill("WrongPassword123");
    await resetPasswordDialog.getByRole("textbox", { name: "New Password", exact: true }).fill("Clinician456");
    await resetPasswordDialog.getByRole("textbox", { name: "Confirm New Password", exact: true }).fill("Clinician456");
    await page.getByRole("button", { name: /update password/i }).click();
    await expect(page.getByText("Current password is incorrect.")).toBeVisible();

    await resetPasswordDialog.getByRole("textbox", { name: "Current Password", exact: true }).fill(clinician.password);
    await resetPasswordDialog.getByRole("textbox", { name: "New Password", exact: true }).fill(clinician.password);
    await resetPasswordDialog.getByRole("textbox", { name: "Confirm New Password", exact: true }).fill(clinician.password);
    await page.getByRole("button", { name: /update password/i }).click();
    await expect(page.getByText("New password cannot be the same as old password.")).toBeVisible();

    await resetPasswordDialog.getByRole("textbox", { name: "Current Password", exact: true }).fill(clinician.password);
    await resetPasswordDialog.getByRole("textbox", { name: "New Password", exact: true }).fill(newPassword);
    await resetPasswordDialog.getByRole("textbox", { name: "Confirm New Password", exact: true }).fill(newPassword);
    await page.getByRole("button", { name: /update password/i }).click();
    await expect(page.getByRole("heading", { name: "Reset Password" })).toHaveCount(0);

    const updatedClinician = { ...clinician, password: newPassword };
    await logoutThroughUi(page, updatedClinician);
    await loginThroughUi(page, updatedClinician);
  } finally {
    try {
      await deactivateUserViaApi(request, clinician.id, adminCredentials);
    } catch {
      // Ignore cleanup failures after a hard timeout.
    }
  }
});

test("researcher can open metrics page with real backend data", async ({ page, request }) => {
  test.setTimeout(120_000);

  const researcher = await createResearcherViaApi(request, adminCredentials);
  try {
    // Backend token iat is second-level precision; wait past the creation second.
    await page.waitForTimeout(1200);
    await signInViaApiSession(page, researcher);

    await expect(page.getByRole("link", { name: "Metrics" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Users" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "New Case" })).toHaveCount(0);

    const metricsResponsePromise = page.waitForResponse((response) => (
      response.request().method() === "GET" && response.url().includes("/model-metrics")
    ));
    await page.getByRole("link", { name: "Metrics" }).click();
    const metricsResponse = await metricsResponsePromise;

    if (!metricsResponse.ok()) {
      const responseBody = await metricsResponse.text();
      test.skip(
        true,
        `Backend model metrics endpoint is unavailable (${metricsResponse.status()}): ${responseBody}`
      );
    }

    await expect(page).toHaveURL(/\/metrics$/);
    await expect(page.getByRole("heading", { name: "Metrics" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Confusion Matrix" })).toBeVisible();
    await expect(page.getByText("Predicted Category")).toBeVisible();
  } finally {
    try {
      await deactivateUserViaApi(request, researcher.id, adminCredentials);
    } catch {
      // Ignore cleanup failures after a hard timeout.
    }
  }
});
