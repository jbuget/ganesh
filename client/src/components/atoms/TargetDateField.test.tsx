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

  /**
   * The same reading as the reference list: a day gone by is said in words as
   * well as in colour, since a reader who cannot tell red from grey would
   * otherwise be told nothing at all.
   */
  it("says so when the announced day has gone by", () => {
    render(
      <TargetDateField
        value="2026-06-30"
        missionLabel="Portail"
        status="development"
        today={new Date("2026-09-25T10:00:00")}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByText("en retard")).toBeInTheDocument();
  });

  it("never says a service in operations is late", () => {
    render(
      <TargetDateField
        value="2026-06-30"
        missionLabel="Portail"
        status="operations"
        today={new Date("2026-09-25T10:00:00")}
        onChange={vi.fn()}
      />,
    );

    expect(screen.queryByText("en retard")).toBeNull();
  });

  /** A guest reads every sheet of the reference list and posts no date. */
  it("is read and not posted when the reader may not write", async () => {
    const onChange = vi.fn();
    render(
      <TargetDateField
        value="2026-11-30"
        missionLabel="Portail"
        editable={false}
        onChange={onChange}
      />,
    );

    const shown = screen.getByRole("button", { name: /Date annoncée pour Portail/ });
    expect(shown).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: /Retirer la date annoncée/ }),
    ).toBeNull();

    await userEvent.click(shown);

    expect(screen.getByText("30 nov. 2026")).toBeInTheDocument();
    expect(onChange).not.toHaveBeenCalled();
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
