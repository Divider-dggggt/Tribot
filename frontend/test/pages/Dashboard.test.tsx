import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MockedFunction } from "vitest";
import { MemoryRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor, within } from "../test-utils";
import { Dashboard } from "../../src/pages/Dashboard";
import { UserRole } from "../../src/types/user";
import type { DashboardCaseObject } from "../../src/types/case";
import { jsonResponse, signInAs } from "../auth-helpers";

const buildCase = (overrides: Partial<DashboardCaseObject>): DashboardCaseObject => ({
  case_id: 1,
  user_id: 1,
  patient_name: "Alice Smith",
  medicare_number: "1111111111",
  severity_flagged: false,
  resolved_at: null,
  created_at: "2026-04-20T10:00:00Z",
  ats_category: 3,
  ats_source: "model",
  ...overrides,
});

const renderDashboard = () => render(
  <MemoryRouter initialEntries={["/dashboard"]}>
    <Dashboard />
  </MemoryRouter>,
);

describe("Dashboard", () => {
  let fetchMock: MockedFunction<typeof fetch>;

  beforeEach(() => {
    signInAs(UserRole.Clinician);
    fetchMock = vi.fn() as MockedFunction<typeof fetch>;
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the empty-state message when there are no cases", async () => {
    fetchMock.mockImplementation(async () => jsonResponse([]));

    renderDashboard();

    expect(await screen.findByText("No cases yet")).toBeInTheDocument();
  });

  it("renders open cases with patient name and Medicare number", async () => {
    fetchMock.mockImplementation(async () => jsonResponse([
      buildCase({ case_id: 1, patient_name: "Alice Smith", medicare_number: "1111111111" }),
      buildCase({ case_id: 2, patient_name: "Bob Jones", medicare_number: "2222222222", ats_category: 2 }),
    ]));

    renderDashboard();

    expect(await screen.findByText("Alice Smith")).toBeInTheDocument();
    expect(screen.getByText("Bob Jones")).toBeInTheDocument();
    expect(screen.getByText("1111111111")).toBeInTheDocument();
    expect(screen.getByText("2222222222")).toBeInTheDocument();
  });

  it("requests resolved cases when switching the toggle", async () => {
    fetchMock.mockImplementation(async () => jsonResponse([]));

    renderDashboard();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/cases",
        expect.anything(),
      );
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Resolved" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/cases?resolved=true",
        expect.anything(),
      );
    });
    expect(screen.getByText("Resolved Cases")).toBeInTheDocument();
  });

  it("calls the resolve endpoint when a clinician clicks the resolve action", async () => {
    fetchMock.mockImplementation(async () => jsonResponse([
      buildCase({ case_id: 7, patient_name: "Alice Smith" }),
    ]));

    renderDashboard();

    const row = (await screen.findByText("Alice Smith")).closest("tr");
    expect(row).not.toBeNull();

    const user = userEvent.setup();
    const resolveButton = within(row as HTMLElement).getByRole("button");
    await user.click(resolveButton);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/cases/7/resolve",
        expect.objectContaining({ method: "PATCH" }),
      );
    });
  });

  it("hides the Create New Case button for non-clinician users", async () => {
    signInAs(UserRole.Researcher);
    fetchMock.mockImplementation(async () => jsonResponse([]));

    renderDashboard();

    await screen.findByText("No cases yet");
    expect(screen.queryByRole("button", { name: /create new case/i })).toBeNull();
  });
});
