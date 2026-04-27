import { expect, test } from "@playwright/test";
import { createAccessToken, mockEmptyCases, signInAs } from "./helpers";

test("redirects protected pages to login when the user is not authenticated", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
});

test("logs in a clinician and opens the dashboard", async ({ page }) => {
  await mockEmptyCases(page);
  await page.route("http://localhost:8000/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: createAccessToken("clinician"),
        token_type: "bearer",
        role: "clinician",
      }),
    });
  });

  await page.goto("/login");
  await page.getByLabel(/email/i).fill("clinician@example.com");
  await page.getByPlaceholder("Enter your password").fill("correct-password");
  await page.getByRole("button", { name: "Sign In" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("button", { name: /clinician@example.com/ })).toBeVisible();
});

test("redirects a clinician away from admin-only user management", async ({ page }) => {
  await signInAs(page, "clinician");
  await mockEmptyCases(page);

  await page.goto("/users");

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});
