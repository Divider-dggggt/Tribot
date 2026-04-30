import { beforeAll, beforeEach, describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, within } from "../test-utils";
import { UsersTable } from "../../src/components/UsersTable";
import { adminCredentials, signInViaApiSession } from "../auth-helpers";

describe("UsersTable", () => {
  beforeAll(async () => {
    await signInViaApiSession(adminCredentials);
  });

  beforeEach(async () => {
    await signInViaApiSession(adminCredentials);
  });

  it("renders the users page title and table", async () => {
    render(<UsersTable />);

    expect(await screen.findByRole("heading", { name: "All Users" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "users table" })).toBeInTheDocument();
  });

  it("renders built-in admin account from real backend", async () => {
    render(<UsersTable />);

    expect(await screen.findByText("admin@example.com")).toBeInTheDocument();
    expect(screen.getByText("admin")).toBeInTheDocument();
  });

  it("opens the create user dialog when clicking Add User", async () => {
    render(<UsersTable />);

    await screen.findByRole("heading", { name: "All Users" });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Add User" }));

    expect(await screen.findByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  it("hides the deactivate action for the current admin's own row", async () => {
    render(<UsersTable />);

    const selfRow = (await screen.findByText(adminCredentials.email)).closest("tr") as HTMLElement;
    expect(selfRow).toBeTruthy();
    const deactivateButtons = within(selfRow).queryAllByRole("button", { name: "Deactivate User" });
    expect(deactivateButtons).toHaveLength(0);
    const editButtons = within(selfRow).queryAllByRole("button", { name: "Edit User" });
    expect(editButtons.length).toBeGreaterThanOrEqual(1);
    expect(localStorage.getItem("user_email")).toBe(adminCredentials.email);
    expect(localStorage.getItem("access_token")).toBeTruthy();
    expect(localStorage.getItem("user_role")).toBe("admin");
  });
});
