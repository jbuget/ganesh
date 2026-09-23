import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PresenceWeek } from "@/components/molecules/PresenceWeek";
import { AT_THE_OFFICE } from "@/lib/presence";

describe("reading a colleague's week", () => {
  it("says where each day is spent", () => {
    render(<PresenceWeek week={{ ...AT_THE_OFFICE, wednesday: "REMOTE" }} />);

    expect(screen.getByLabelText("Mercredi : télétravail")).toBeInTheDocument();
    expect(screen.getByLabelText("Lundi : sur site")).toBeInTheDocument();
  });

  it("offers nothing to change", () => {
    render(<PresenceWeek week={AT_THE_OFFICE} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("saying one's own", () => {
  it("walks a day from the office to home", async () => {
    const onChange = vi.fn();
    render(<PresenceWeek week={AT_THE_OFFICE} editable onChange={onChange} />);

    await userEvent.click(screen.getByLabelText(/^Mercredi/));

    expect(onChange).toHaveBeenCalledWith({
      ...AT_THE_OFFICE,
      wednesday: "REMOTE",
    });
  });

  it("comes back round to the office", async () => {
    const onChange = vi.fn();
    render(
      <PresenceWeek
        week={{ ...AT_THE_OFFICE, friday: "AWAY" }}
        editable
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByLabelText(/^Vendredi/));

    expect(onChange).toHaveBeenCalledWith(AT_THE_OFFICE);
  });
});
