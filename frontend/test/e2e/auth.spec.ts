import { expect, test, type Page } from "@playwright/test";

type TestRole = "admin" | "clinician" | "researcher";

const encodeJwtPart = (value: unknown): string => (
  Buffer.from(JSON.stringify(value)).toString("base64url")
);

const createAccessToken = (role: TestRole): string => {
  const header = encodeJwtPart({ alg: "none", typ: "JWT" });
  const payload = encodeJwtPart({
    exp: Math.floor(Date.now() / 1000) + 60 * 60,
    user_id: 1,
    role,
  });

  return `${header}.${payload}.test-signature`;
};

const mockEmptyCases = async (page: Page): Promise<void> => {
  await page.route("http://localhost:8000/cases**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
};

const signInAs = async (page: Page, role: TestRole): Promise<void> => {
  const token = createAccessToken(role);

  await page.addInitScript(({ accessToken, userRole }) => {
    window.localStorage.setItem("access_token", accessToken);
    window.localStorage.setItem("token_type", "bearer");
    window.localStorage.setItem("user_role", userRole);
    window.localStorage.setItem("user_email", `${userRole}@example.com`);
  }, { accessToken: token, userRole: role });
};

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
