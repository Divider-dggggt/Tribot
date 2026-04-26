import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { AuthLogo } from "../../src/components/AuthLogo";

describe("AuthLogo", () => {
  it("renders the product name and subtitle", () => {
    render(<AuthLogo subtitle="Clinician Triage System" />);

    expect(screen.getByText("TRIBOT")).toBeInTheDocument();
    expect(screen.getByText("Clinician Triage System")).toBeInTheDocument();
  });
});
