import type { Page } from "@playwright/test";

export type TestRole = "admin" | "clinician" | "researcher";

const encodeJwtPart = (value: unknown): string => (
  Buffer.from(JSON.stringify(value)).toString("base64url")
);

export const createAccessToken = (role: TestRole): string => {
  const header = encodeJwtPart({ alg: "none", typ: "JWT" });
  const payload = encodeJwtPart({
    exp: Math.floor(Date.now() / 1000) + 60 * 60,
    user_id: 1,
    role,
  });
  return `${header}.${payload}.test-signature`;
};

export const signInAs = async (page: Page, role: TestRole): Promise<void> => {
  const token = createAccessToken(role);

  await page.addInitScript(({ accessToken, userRole }) => {
    window.localStorage.setItem("access_token", accessToken);
    window.localStorage.setItem("token_type", "bearer");
    window.localStorage.setItem("user_role", userRole);
    window.localStorage.setItem("user_email", `${userRole}@example.com`);
  }, { accessToken: token, userRole: role });
};

export const mockEmptyCases = async (page: Page): Promise<void> => {
  await page.route("http://localhost:8000/cases**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
};
