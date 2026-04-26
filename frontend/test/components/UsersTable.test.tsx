import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MockedFunction } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor, within } from "../test-utils";
import { UsersTable } from "../../src/components/UsersTable";
import { UserRole, type User } from "../../src/types/user";
import { jsonResponse, signInAs } from "../auth-helpers";

const buildUser = (overrides: Partial<User>): User => ({
  id: 10,
  name: "Alice Admin",
  email: "alice@example.com",
  role: UserRole.Admin,
  created_at: "2026-04-10T10:00:00Z",
  ...overrides,
});

describe("UsersTable", () => {
  let fetchMock: MockedFunction<typeof fetch>;

  beforeEach(() => {
    signInAs(UserRole.Admin, { userId: 1 });
    fetchMock = vi.fn() as MockedFunction<typeof fetch>;
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the empty-state message when no users exist", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));

    render(<UsersTable />);

    expect(await screen.findByText("No users found")).toBeInTheDocument();
  });

  it("renders each user with name, email, and role", async () => {
    fetchMock.mockResolvedValue(jsonResponse([
      buildUser({ id: 10, name: "Alice Admin", email: "alice@example.com", role: UserRole.Admin }),
      buildUser({ id: 20, name: "Chris Clinician", email: "chris@example.com", role: UserRole.Clinician }),
    ]));

    render(<UsersTable />);

    expect(await screen.findByText("Alice Admin")).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("Chris Clinician")).toBeInTheDocument();
    expect(screen.getByText("chris@example.com")).toBeInTheDocument();
    expect(screen.getByText(UserRole.Admin)).toBeInTheDocument();
    expect(screen.getByText(UserRole.Clinician)).toBeInTheDocument();
  });

  it("opens the create user dialog when clicking Add User", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));

    render(<UsersTable />);

    await screen.findByText("No users found");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Add User" }));

    expect(await screen.findByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  it("hides the deactivate action for the current admin's own row", async () => {
    fetchMock.mockResolvedValue(jsonResponse([
      buildUser({ id: 1, name: "Me Admin", email: "me@example.com", role: UserRole.Admin }),
      buildUser({ id: 20, name: "Chris Clinician", email: "chris@example.com", role: UserRole.Clinician }),
    ]));

    render(<UsersTable />);

    const selfRow = (await screen.findByText("Me Admin")).closest("tr") as HTMLElement;
    const otherRow = (screen.getByText("Chris Clinician")).closest("tr") as HTMLElement;

    expect(within(selfRow).getAllByRole("button")).toHaveLength(1);
    expect(within(otherRow).getAllByRole("button")).toHaveLength(2);
  });
});
