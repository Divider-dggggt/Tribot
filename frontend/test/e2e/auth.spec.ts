import { expect, test } from "@playwright/test";
import { adminCredentials, loginThroughUi } from "./helpers";

test("redirects protected pages to login when the user is not authenticated", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
});

test("logs in with the built-in admin account and opens dashboard", async ({ page }) => {
  await loginThroughUi(page, adminCredentials);

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("button", { name: /admin@example\.com/i })).toBeVisible();
});

test("redirects admin away from clinician-only case creation page", async ({ page }) => {
  await loginThroughUi(page, adminCredentials);

  await page.goto("/new-case");

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});
