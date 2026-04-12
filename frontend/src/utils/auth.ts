import { jwtDecode } from "jwt-decode";
import { AccessTokenPayload } from "../types/user";

const SESSION_STORAGE_KEYS = ["access_token", "token_type", "user_role", "user_email"] as const;
const SESSION_EXPIRED_MESSAGE = "Session expired. Please sign in again.";

interface ValidSession {
  token: string;
  payload: AccessTokenPayload;
}

const decodeTokenPayload = (token: string): AccessTokenPayload | null => {
  try {
    return jwtDecode<AccessTokenPayload>(token);
  } catch {
    return null;
  }
};

const isTokenExpired = (payload: AccessTokenPayload): boolean => (
  payload.exp * 1000 <= Date.now()
);

const getValidSession = (): ValidSession | null => {
  const token = localStorage.getItem("access_token");
  if (token == null) {
    return null;
  }

  const payload = decodeTokenPayload(token);
  if (payload == null || isTokenExpired(payload)) {
    return null;
  }

  return { token, payload };
};

const redirectToLogin = (): void => {
  if (window.location.pathname === "/login") {
    return;
  }

  window.location.replace("/login");
};

export const clearAuthSession = (): void => {
  SESSION_STORAGE_KEYS.forEach((key) => {
    localStorage.removeItem(key);
  });
};

export const isAuthenticated = (): boolean => {
  const session = getValidSession();
  if (session == null) {
    clearAuthSession();
    return false;
  }

  return true;
};

export const getDecodedToken = (): AccessTokenPayload | null => {
  return getValidSession()?.payload ?? null;
};

export const getAccessToken = (): string | null => getValidSession()?.token ?? null;

export const handleUnauthorized = (): void => {
  clearAuthSession();
  redirectToLogin();
};

export const fetchWithAuth = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const accessToken = getAccessToken();
  if (accessToken == null) {
    handleUnauthorized();
    throw new Error(SESSION_EXPIRED_MESSAGE);
  }

  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(input, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    handleUnauthorized();
    throw new Error(SESSION_EXPIRED_MESSAGE);
  }

  return response;
};
