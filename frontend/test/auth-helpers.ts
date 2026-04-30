import { UserRole } from "../src/types/user";

const backendBaseUrl = (
  process.env.VITEST_REAL_API_BASE_URL
  ?? process.env.E2E_API_BASE_URL
  ?? process.env.VITE_API_BASE_URL
  ?? "http://localhost:8000"
).replace(/\/+$/, "");

export interface UserCredentials {
  email: string;
  password: string;
}

export interface CreatedUser extends UserCredentials {
  id: number;
  role: UserRole;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
}

interface AccessTokenPayload {
  user_id: number;
  role: UserRole;
  exp: number;
}

export const adminCredentials: UserCredentials = {
  email: process.env.E2E_ADMIN_EMAIL ?? "admin@example.com",
  password: process.env.E2E_ADMIN_PASSWORD ?? "admin123",
};

const decodeBase64Url = (value: string): string => {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(base64.length + ((4 - base64.length % 4) % 4), "=");
  return atob(padded);
};

const decodeAccessTokenPayload = (accessToken: string): AccessTokenPayload => {
  const [, payload] = accessToken.split(".");
  if (payload == null) {
    throw new Error("Access token payload is missing.");
  }
  return JSON.parse(decodeBase64Url(payload)) as AccessTokenPayload;
};

export const clearAuthSession = (): void => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token_type");
  localStorage.removeItem("user_role");
  localStorage.removeItem("user_email");
};

export const loginViaApi = async (credentials: UserCredentials): Promise<LoginResponse> => {
  const response = await fetch(`${backendBaseUrl}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: credentials.email,
      password: credentials.password,
    }),
  });

  if (!response.ok) {
    const bodyText = await response.text();
    throw new Error(`Login failed (${response.status()}): ${bodyText}`);
  }

  const responseBody = await response.json() as LoginResponse;
  if (
    typeof responseBody.access_token !== "string"
    || typeof responseBody.token_type !== "string"
    || typeof responseBody.role !== "string"
  ) {
    throw new Error("Login response is missing required fields.");
  }

  return responseBody;
};

export const signInViaApiSession = async (credentials: UserCredentials): Promise<{
  userId: number;
  role: UserRole;
}> => {
  const loginResponse = await loginViaApi(credentials);
  const payload = decodeAccessTokenPayload(loginResponse.access_token);

  localStorage.setItem("access_token", loginResponse.access_token);
  localStorage.setItem("token_type", loginResponse.token_type);
  localStorage.setItem("user_role", loginResponse.role);
  localStorage.setItem("user_email", credentials.email);

  return {
    userId: payload.user_id,
    role: payload.role,
  };
};

export const createUserViaApi = async (options: {
  role: UserRole;
  namePrefix: string;
  emailPrefix: string;
  password: string;
  adminCreds?: UserCredentials;
}): Promise<CreatedUser> => {
  const {
    role,
    namePrefix,
    emailPrefix,
    password,
    adminCreds = adminCredentials,
  } = options;
  const adminLogin = await loginViaApi(adminCreds);
  const uniqueSuffix = `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
  const email = `${emailPrefix}.${uniqueSuffix}@example.com`;

  const response = await fetch(`${backendBaseUrl}/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${adminLogin.access_token}`,
    },
    body: JSON.stringify({
      name: `${namePrefix} ${uniqueSuffix}`,
      email,
      role,
      password,
    }),
  });

  if (!response.ok) {
    const bodyText = await response.text();
    throw new Error(`Create user failed (${response.status()}): ${bodyText}`);
  }

  const responseBody = await response.json() as { id?: number };
  if (typeof responseBody.id !== "number") {
    throw new Error("Create user response did not include id.");
  }

  return {
    id: responseBody.id,
    email,
    password,
    role,
  };
};

export const deactivateUserViaApi = async (
  userId: number,
  adminCreds: UserCredentials = adminCredentials,
): Promise<void> => {
  const adminLogin = await loginViaApi(adminCreds);
  const response = await fetch(`${backendBaseUrl}/users/${userId}/deactivate`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${adminLogin.access_token}`,
    },
  });

  if (!response.ok && response.status !== 404) {
    const bodyText = await response.text();
    throw new Error(`Deactivate user failed (${response.status}): ${bodyText}`);
  }
};
