import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WeekPatternPicker } from "@/components/atoms/WeekPatternPicker";
import { FULL_TIME } from "@/lib/rhythm";

describe("reading a rhythm", () => {
  it("says what each day is worth, for whoever cannot see the row", () => {
    render(<WeekPatternPicker pattern={{ ...FULL_TIME, wednesday: 0 }} />);

    expect(screen.getByLabelText("Mercredi : non travaillé")).toBeInTheDocument();
    expect(screen.getByLabelText("Lundi : journée entière")).toBeInTheDocument();
  });

  it("offers no button on a colleague's rhythm", () => {
    render(<WeekPatternPicker pattern={FULL_TIME} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("declaring one's own", () => {
  it("takes a day down rather than up", async () => {
    const onChange = vi.fn();
    render(<WeekPatternPicker pattern={FULL_TIME} editable onChange={onChange} />);

    await userEvent.click(screen.getByLabelText(/^Mercredi/));

    expect(onChange).toHaveBeenCalledWith({ ...FULL_TIME, wednesday: 0.5 });
  });

  it("goes round to a full day again", async () => {
    const onChange = vi.fn();
    render(
      <WeekPatternPicker
        pattern={{ ...FULL_TIME, wednesday: 0 }}
        editable
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByLabelText(/^Mercredi/));

    expect(onChange).toHaveBeenCalledWith(FULL_TIME);
  });
});
