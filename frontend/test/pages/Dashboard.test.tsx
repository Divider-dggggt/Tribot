import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "../test-utils";
import { Dashboard } from "../../src/pages/Dashboard";
import { UserRole } from "../../src/types/user";
import {
  clearAuthSession,
  createUserViaApi,
  deactivateUserViaApi,
  signInViaApiSession,
  type CreatedUser,
} from "../auth-helpers";

const renderDashboard = () => render(
  <MemoryRouter initialEntries={["/dashboard"]}>
    <Dashboard />
  </MemoryRouter>,
);

const waitForCasesToFinishLoading = async (): Promise<void> => {
  await waitFor(() => {
    const hasEmptyState = screen.queryByText("No cases yet") != null;
    const rows = screen.getAllByRole("row");
    const hasCaseRows = rows.length > 2;
    if (hasEmptyState || hasCaseRows) {
      return;
    }
    throw new Error("Waiting for cases table to finish loading.");
  }, { timeout: 15_000 });
};

describe("Dashboard", () => {
  let clinician: CreatedUser;
  let researcher: CreatedUser;

  beforeAll(async () => {
    clinician = await createUserViaApi({
      role: UserRole.Clinician,
      namePrefix: "Vitest Clinician Dashboard",
      emailPrefix: "vitest.dashboard.clinician",
      password: "Clinician123",
    });
    researcher = await createUserViaApi({
      role: UserRole.Researcher,
      namePrefix: "Vitest Researcher Dashboard",
      emailPrefix: "vitest.dashboard.researcher",
      password: "Researcher123",
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
    await deactivateUserViaApi(researcher.id);
  });

  it("renders dashboard heading and main controls for clinician", async () => {
    renderDashboard();

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create new case/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resolved" })).toBeInTheDocument();
    await waitForCasesToFinishLoading();
  });

  it("allows switching to resolved view", async () => {
    renderDashboard();
    await screen.findByRole("heading", { name: "Dashboard" });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Resolved" }));

    expect(await screen.findByText("Resolved Cases")).toBeInTheDocument();
    await waitForCasesToFinishLoading();
  });

  it("hides the Create New Case button for non-clinician users", async () => {
    await signInViaApiSession(researcher);

    renderDashboard();

    await screen.findByRole("heading", { name: "Dashboard" });
    expect(screen.queryByRole("button", { name: /create new case/i })).toBeNull();
    await waitForCasesToFinishLoading();
  });
});
