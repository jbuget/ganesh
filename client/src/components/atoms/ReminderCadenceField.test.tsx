import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReminderCadenceField } from "@/components/atoms/ReminderCadenceField";
import { ReminderCadence } from "@/lib/api/generated/model";

describe("ReminderCadenceField", () => {
  it("offers the three cadences", () => {
    render(<ReminderCadenceField value={ReminderCadence.DAILY} onChange={vi.fn()} />);

    expect(screen.getAllByRole("radio")).toHaveLength(3);
    expect(screen.getByLabelText(/Chaque jour/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Chaque semaine/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Jamais/)).toBeInTheDocument();
  });

  it("shows which one is in force", () => {
    render(<ReminderCadenceField value={ReminderCadence.WEEKLY} onChange={vi.fn()} />);

    expect(screen.getByLabelText(/Chaque semaine/)).toBeChecked();
    expect(screen.getByLabelText(/Chaque jour/)).not.toBeChecked();
  });

  it("hands back the cadence one picks", () => {
    const onChange = vi.fn();
    render(<ReminderCadenceField value={ReminderCadence.DAILY} onChange={onChange} />);

    fireEvent.click(screen.getByLabelText(/Jamais/));

    expect(onChange).toHaveBeenCalledWith(ReminderCadence.NEVER);
  });

  it("says what each cadence means, not only its name", () => {
    render(<ReminderCadenceField value={ReminderCadence.DAILY} onChange={vi.fn()} />);

    expect(
      screen.getByText(/uniquement si quelque chose vous attend/),
    ).toBeInTheDocument();
  });

  it("takes no second answer while the first is on its way", async () => {
    const onChange = vi.fn();
    render(
      <ReminderCadenceField
        value={ReminderCadence.DAILY}
        onChange={onChange}
        isSaving
      />,
    );

    expect(screen.getByLabelText(/Jamais/)).toBeDisabled();
    await userEvent.click(screen.getByLabelText(/Jamais/));

    expect(onChange).not.toHaveBeenCalled();
  });
});
