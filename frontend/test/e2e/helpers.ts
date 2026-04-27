import { expect, type APIRequestContext, type Page } from "@playwright/test";

const BACKEND_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://localhost:8000";

export interface UserCredentials {
  email: string;
  password: string;
}

export interface CreatedClinician extends UserCredentials {
  id: number;
}

export const adminCredentials: UserCredentials = {
  email: process.env.E2E_ADMIN_EMAIL ?? "admin@example.com",
  password: process.env.E2E_ADMIN_PASSWORD ?? "admin123",
};

const escapeRegex = (value: string): string => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const getAdminAccessToken = async (
  request: APIRequestContext,
  credentials: UserCredentials = adminCredentials,
): Promise<string> => {
  const loginResponse = await request.post(`${BACKEND_BASE_URL}/login`, {
    data: {
      email: credentials.email,
      password: credentials.password,
    },
  });

  if (!loginResponse.ok()) {
    const details = await loginResponse.text();
    throw new Error(`Admin login failed (${loginResponse.status()}): ${details}`);
  }

  const loginBody = await loginResponse.json() as { access_token?: string };
  if (typeof loginBody.access_token !== "string" || loginBody.access_token.length === 0) {
    throw new Error("Admin login response did not include access_token.");
  }

  return loginBody.access_token;
};

export const loginThroughUi = async (
  page: Page,
  credentials: UserCredentials,
): Promise<void> => {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(credentials.email);
  await page.getByPlaceholder("Enter your password").fill(credentials.password);
  await page.getByRole("button", { name: "Sign In" }).click();

  await expect(page).toHaveURL(/\/dashboard(?:\?.*)?$/);
};

export const signInViaApiSession = async (
  page: Page,
  credentials: UserCredentials,
): Promise<void> => {
  const loginResponse = await page.request.post(`${BACKEND_BASE_URL}/login`, {
    data: {
      email: credentials.email,
      password: credentials.password,
    },
  });

  if (!loginResponse.ok()) {
    const details = await loginResponse.text();
    throw new Error(`UI session bootstrap login failed (${loginResponse.status()}): ${details}`);
  }

  const loginBody = await loginResponse.json() as {
    access_token?: string;
    token_type?: string;
    role?: string;
  };

  if (
    typeof loginBody.access_token !== "string" ||
    typeof loginBody.token_type !== "string" ||
    typeof loginBody.role !== "string"
  ) {
    throw new Error("UI session bootstrap login response is missing required fields.");
  }

  await page.goto("/login");
  await page.evaluate(({ accessToken, tokenType, role, email }) => {
    window.localStorage.setItem("access_token", accessToken);
    window.localStorage.setItem("token_type", tokenType);
    window.localStorage.setItem("user_role", role);
    window.localStorage.setItem("user_email", email);
  }, {
    accessToken: loginBody.access_token,
    tokenType: loginBody.token_type,
    role: loginBody.role,
    email: credentials.email,
  });
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/dashboard(?:\?.*)?$/);
};

export const logoutThroughUi = async (
  page: Page,
  credentials: UserCredentials,
): Promise<void> => {
  const accountButton = page.getByRole("button", {
    name: new RegExp(escapeRegex(credentials.email), "i"),
  });

  await accountButton.click();
  await page.getByRole("menuitem", { name: /logout/i }).click();
  await expect(page).toHaveURL(/\/login$/);
};

export const createClinicianViaApi = async (
  request: APIRequestContext,
  adminCreds: UserCredentials = adminCredentials,
): Promise<CreatedClinician> => {
  const adminAccessToken = await getAdminAccessToken(request, adminCreds);
  const uniqueSuffix = `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
  const clinicianPassword = "Clinician123";
  const clinicianEmail = `clinician.${uniqueSuffix}@example.com`;

  const createUserResponse = await request.post(`${BACKEND_BASE_URL}/users`, {
    headers: {
      Authorization: `Bearer ${adminAccessToken}`,
      "Content-Type": "application/json",
    },
    data: {
      name: `E2E Clinician ${uniqueSuffix}`,
      email: clinicianEmail,
      role: "clinician",
      password: clinicianPassword,
    },
  });

  if (!createUserResponse.ok()) {
    const details = await createUserResponse.text();
    throw new Error(`Create clinician failed (${createUserResponse.status()}): ${details}`);
  }

  const createdUser = await createUserResponse.json() as { id?: number };
  if (typeof createdUser.id !== "number") {
    throw new Error("Create clinician response did not include user id.");
  }

  return {
    id: createdUser.id,
    email: clinicianEmail,
    password: clinicianPassword,
  };
};

export const deactivateUserViaApi = async (
  request: APIRequestContext,
  userId: number,
  adminCreds: UserCredentials = adminCredentials,
): Promise<void> => {
  const adminAccessToken = await getAdminAccessToken(request, adminCreds);
  const deactivateResponse = await request.patch(`${BACKEND_BASE_URL}/users/${userId}/deactivate`, {
    headers: {
      Authorization: `Bearer ${adminAccessToken}`,
    },
  });

  if (!deactivateResponse.ok() && deactivateResponse.status() !== 404) {
    const details = await deactivateResponse.text();
    throw new Error(`Deactivate user failed (${deactivateResponse.status()}): ${details}`);
  }
};
