import type { UserRole } from "../src/types/user";

const base64UrlEncode = (value: unknown): string => (
  btoa(JSON.stringify(value))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "")
);

export const createAccessToken = (role: UserRole | string, userId = 1): string => {
  const header = base64UrlEncode({ alg: "none", typ: "JWT" });
  const payload = base64UrlEncode({
    exp: Math.floor(Date.now() / 1000) + 60 * 60,
    user_id: userId,
    role,
  });
  return `${header}.${payload}.test-signature`;
};

interface SignInOptions {
  userId?: number;
  email?: string;
}

export const signInAs = (role: UserRole | string, options: SignInOptions = {}): void => {
  const userId = options.userId ?? 1;
  const email = options.email ?? `${String(role)}@example.com`;
  localStorage.setItem("access_token", createAccessToken(role, userId));
  localStorage.setItem("token_type", "bearer");
  localStorage.setItem("user_role", String(role));
  localStorage.setItem("user_email", email);
};

export const jsonResponse = (body: unknown, status = 200): Response => (
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  })
);
