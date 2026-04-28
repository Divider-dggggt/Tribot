import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "../test-utils";
import { LoginPage } from "../../src/pages/LoginPage";
import { adminCredentials, clearAuthSession } from "../auth-helpers";

const renderLoginPage = () => render(
  <MemoryRouter initialEntries={["/login"]}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<div>Dashboard route</div>} />
    </Routes>
  </MemoryRouter>,
);

describe("LoginPage", () => {
  afterEach(() => {
    clearAuthSession();
  });

  it("shows validation messages when required fields are empty", async () => {
    const user = userEvent.setup();

    renderLoginPage();

    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(await screen.findByText("Please enter your email.")).toBeInTheDocument();
    expect(screen.getByText("Please enter your password.")).toBeInTheDocument();
  });

  it("shows the API error when credentials are rejected", async () => {
    const user = userEvent.setup();

    renderLoginPage();

    await user.type(screen.getByLabelText(/email/i), `invalid-${Date.now()}@example.com`);
    await user.type(screen.getByPlaceholderText("Enter your password"), "wrong-password-123");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(await screen.findByText(/Invalid email or password\.?/i)).toBeInTheDocument();
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("stores the session and navigates to dashboard after a successful login", async () => {
    const user = userEvent.setup();

    renderLoginPage();

    await user.type(screen.getByLabelText(/email/i), adminCredentials.email);
    await user.type(screen.getByPlaceholderText("Enter your password"), adminCredentials.password);
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(localStorage.getItem("access_token")).toBeTruthy();
      expect(localStorage.getItem("token_type")).toBe("bearer");
      expect(localStorage.getItem("user_role")).toBe("admin");
      expect(localStorage.getItem("user_email")).toBe(adminCredentials.email);
    });
    expect(await screen.findByText("Dashboard route", {}, { timeout: 2000 })).toBeInTheDocument();
  });
});
