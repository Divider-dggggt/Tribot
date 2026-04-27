import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MockedFunction } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "../test-utils";
import { LoginPage } from "../../src/pages/LoginPage";

const jsonResponse = (body: unknown, status = 200): Response => (
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  })
);

const renderLoginPage = () => render(
  <MemoryRouter initialEntries={["/login"]}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<div>Dashboard route</div>} />
    </Routes>
  </MemoryRouter>,
);

describe("LoginPage", () => {
  let fetchMock: MockedFunction<typeof fetch>;

  beforeEach(() => {
    fetchMock = vi.fn() as MockedFunction<typeof fetch>;
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows validation messages when required fields are empty", async () => {
    const user = userEvent.setup();

    renderLoginPage();

    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(await screen.findByText("Please enter your email.")).toBeInTheDocument();
    expect(screen.getByText("Please enter your password.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows the API error when credentials are rejected", async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Invalid email or password." }, 401));

    renderLoginPage();

    await user.type(screen.getByLabelText(/email/i), "clinician@example.com");
    await user.type(screen.getByPlaceholderText("Enter your password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("stores the session and navigates to dashboard after a successful login", async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(jsonResponse({
      access_token: "test-access-token",
      token_type: "bearer",
      role: "clinician",
    }));

    renderLoginPage();

    await user.type(screen.getByLabelText(/email/i), " clinician@example.com ");
    await user.type(screen.getByPlaceholderText("Enter your password"), "correct-password");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(localStorage.getItem("access_token")).toBe("test-access-token");
      expect(localStorage.getItem("token_type")).toBe("bearer");
      expect(localStorage.getItem("user_role")).toBe("clinician");
      expect(localStorage.getItem("user_email")).toBe("clinician@example.com");
    });
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/login", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({
        email: "clinician@example.com",
        password: "correct-password",
      }),
    }));
    expect(await screen.findByText("Dashboard route", {}, { timeout: 2000 })).toBeInTheDocument();
  });
});
