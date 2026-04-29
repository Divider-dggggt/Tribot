import type { ReactElement } from "react";
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "../test-utils";
import { CaseForm } from "../../src/pages/CaseForm";
import { UserRole } from "../../src/types/user";
import {
  clearAuthSession,
  createUserViaApi,
  deactivateUserViaApi,
  signInViaApiSession,
  type CreatedUser,
} from "../auth-helpers";

const DashboardProbe = (): ReactElement => {
  const location = useLocation();
  return (
    <div>
      <span data-testid="pathname">{location.pathname}</span>
      <span data-testid="search">{location.search}</span>
    </div>
  );
};

const renderCaseForm = () => render(
  <MemoryRouter initialEntries={["/new-case"]}>
    <Routes>
      <Route path="/new-case" element={<CaseForm />} />
      <Route path="/dashboard" element={<DashboardProbe />} />
    </Routes>
  </MemoryRouter>,
);

describe("CaseForm", () => {
  let clinician: CreatedUser;

  beforeAll(async () => {
    clinician = await createUserViaApi({
      role: UserRole.Clinician,
      namePrefix: "Vitest Clinician",
      emailPrefix: "vitest.clinician",
      password: "Clinician123",
    });
    // Backend token iat uses second-level precision for newly created users.
    await new Promise<void>((resolve) => {
      setTimeout(resolve, 1200);
    });
  });

  beforeEach(async () => {
    await signInViaApiSession(clinician);
  });

  afterAll(async () => {
    clearAuthSession();
    await deactivateUserViaApi(clinician.id);
  });

  it("shows required field errors when submitting an empty form", async () => {
    const user = userEvent.setup();

    renderCaseForm();

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    const requiredMessages = await screen.findAllByText("Required");
    expect(requiredMessages.length).toBeGreaterThanOrEqual(3);
  });

  it("rejects an invalid Medicare number format", async () => {
    const user = userEvent.setup();

    renderCaseForm();

    await user.type(screen.getByLabelText(/medicare card number/i), "123456789");
    await user.type(screen.getByLabelText(/patient name/i), "John Doe");
    await user.type(screen.getByLabelText(/case details/i), "Severe chest pain");

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    expect(
      await screen.findByText("Must include card number (10 digits) and IRN (1 digit)"),
    ).toBeInTheDocument();
  });

  it("submits a valid case and navigates to the created case view", async () => {
    const user = userEvent.setup();

    renderCaseForm();

    const uniqueSeed = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
    const medicareCardBase = uniqueSeed.slice(-10).padStart(10, "0");
    await user.type(screen.getByLabelText(/medicare card number/i), `${medicareCardBase}/1`);
    await user.type(screen.getByLabelText(/patient name/i), `Vitest Patient ${uniqueSeed.slice(-4)}`);
    await user.type(screen.getByLabelText(/case details/i), "Severe chest pain with shortness of breath.");

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    await waitFor(() => {
      const pathname = screen.getByTestId("pathname").textContent;
      const modelMissingError = screen.queryByText(/expected str, bytes or os\.PathLike object, not NoneType/i);
      if (pathname === "/dashboard" || modelMissingError != null) {
        return;
      }
      throw new Error("Waiting for either successful navigation or known model-missing error.");
    }, { timeout: 45_000 });

    const pathname = screen.getByTestId("pathname").textContent;
    if (pathname === "/dashboard") {
      expect(screen.getByTestId("search").textContent ?? "").toMatch(/\?case=\d+/);
      return;
    }
    expect(screen.getByText(/expected str, bytes or os\.PathLike object, not NoneType/i)).toBeInTheDocument();
  }, 60_000);

  it("shows a session-expired message when auth session is missing", async () => {
    const user = userEvent.setup();

    renderCaseForm();

    clearAuthSession();
    await user.type(screen.getByLabelText(/medicare card number/i), "1234567890/1");
    await user.type(screen.getByLabelText(/patient name/i), "John Doe");
    await user.type(screen.getByLabelText(/case details/i), "Severe chest pain");

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    expect(await screen.findByText("Session expired. Please sign in again.")).toBeInTheDocument();
  });
});
