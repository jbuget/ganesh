import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TargetDateField } from "./TargetDateField";

describe("TargetDateField", () => {
  it("offers to date a mission that carries no date", () => {
    render(<TargetDateField value={null} missionLabel="Portail" onChange={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: /Date annoncée pour Portail/ }),
    ).toHaveTextContent("Dater");
  });

  it("shows the date in words rather than in ISO", () => {
    render(
      <TargetDateField value="2026-11-30" missionLabel="Portail" onChange={vi.fn()} />,
    );

    expect(screen.getByText("30 nov. 2026")).toBeInTheDocument();
  });

  it("posts the date typed", async () => {
    const onChange = vi.fn();
    render(<TargetDateField value={null} missionLabel="Portail" onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Date annoncée/ }));
    const field = screen.getByLabelText("Date annoncée pour Portail");
    await userEvent.type(field, "2026-11-30");
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith("2026-11-30");
  });

  it("withdraws a date without asking twice", async () => {
    const onChange = vi.fn();
    render(
      <TargetDateField value="2026-11-30" missionLabel="Portail" onChange={onChange} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: /Retirer la date annoncée/ }),
    );

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("leaves the date alone when nothing changed", async () => {
    const onChange = vi.fn();
    render(
      <TargetDateField value="2026-11-30" missionLabel="Portail" onChange={onChange} />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Date annoncée/ }));
    await userEvent.tab();

    expect(onChange).not.toHaveBeenCalled();
  });
});
