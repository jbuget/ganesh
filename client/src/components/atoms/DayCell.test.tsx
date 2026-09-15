import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { cycleDayValue, DayCell } from "./DayCell";

describe("cycleDayValue", () => {
  it("passe de vide a une demi-journee", () => {
    expect(cycleDayValue(0)).toBe(0.5);
  });

  it("passe d'une demi-journee a une journee complete", () => {
    expect(cycleDayValue(0.5)).toBe(1);
  });

  it("revient a vide apres une journee complete", () => {
    expect(cycleDayValue(1)).toBe(0);
  });
});

describe("DayCell", () => {
  it("notifie la valeur suivante au clic", async () => {
    const onChange = vi.fn();
    render(
      <DayCell value={0} isOffDay={false} isReadOnly={false} onChange={onChange} />,
    );

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).toHaveBeenCalledWith(0.5);
  });

  it("n'est pas cliquable quand le mois est verrouille", async () => {
    const onChange = vi.fn();
    render(<DayCell value={1} isOffDay={false} isReadOnly onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });
});
