import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "../test-utils";
import { PasswordField } from "../../src/components/PasswordField";

describe("PasswordField", () => {
  it("toggles password visibility", async () => {
    const user = userEvent.setup();

    render(<PasswordField label="Password" />);

    const input = screen.getByLabelText("Password");
    expect(input).toHaveAttribute("type", "password");

    await user.click(screen.getByLabelText("Show password"));
    expect(input).toHaveAttribute("type", "text");

    await user.click(screen.getByLabelText("Hide password"));
    expect(input).toHaveAttribute("type", "password");
  });
});
