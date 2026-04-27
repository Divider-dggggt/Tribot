import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MockedFunction } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "../test-utils";
import { CaseForm } from "../../src/pages/CaseForm";
import { UserRole } from "../../src/types/user";
import { jsonResponse, signInAs } from "../auth-helpers";

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
  let fetchMock: MockedFunction<typeof fetch>;

  beforeEach(() => {
    signInAs(UserRole.Clinician);
    fetchMock = vi.fn() as MockedFunction<typeof fetch>;
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows required field errors when submitting an empty form", async () => {
    const user = userEvent.setup();

    renderCaseForm();

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    const requiredMessages = await screen.findAllByText("Required");
    expect(requiredMessages.length).toBeGreaterThanOrEqual(3);
    expect(fetchMock).not.toHaveBeenCalled();
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
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("submits a valid case and navigates to the created case view", async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(jsonResponse({
      case_id: 42,
      severity_flagged: false,
      soap_summary: "Summary",
      ats_classification: 3,
      confidence_score: 0.82,
      flagged_keywords: null,
    }));

    renderCaseForm();

    await user.type(screen.getByLabelText(/medicare card number/i), "1234567890/1");
    await user.type(screen.getByLabelText(/patient name/i), "John Doe");
    await user.type(screen.getByLabelText(/case details/i), "Severe chest pain");

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    const [requestUrl, requestInit] = fetchMock.mock.calls[0];
    expect(requestUrl).toBe("http://localhost:8000/triage");
    expect(requestInit?.method).toBe("POST");
    const parsedBody = JSON.parse(String(requestInit?.body ?? ""));
    expect(parsedBody).toEqual({
      patient_name: "John Doe",
      medicare_number: "12345678901",
      case_dialogue: "Severe chest pain",
    });

    expect(await screen.findByTestId("pathname")).toHaveTextContent("/dashboard");
    expect(screen.getByTestId("search")).toHaveTextContent("?case=42");
  });

  it("shows a server error message when submission fails", async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Triage service unavailable" }, 503));

    renderCaseForm();

    await user.type(screen.getByLabelText(/medicare card number/i), "1234567890/1");
    await user.type(screen.getByLabelText(/patient name/i), "John Doe");
    await user.type(screen.getByLabelText(/case details/i), "Severe chest pain");

    await user.click(screen.getByRole("button", { name: /submit for triage/i }));

    expect(await screen.findByText("Triage service unavailable")).toBeInTheDocument();
  });
});
