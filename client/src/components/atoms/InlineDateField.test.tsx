import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { InlineDateField } from "./InlineDateField";

describe("InlineDateField", () => {
  it("says what the empty field is waiting for", () => {
    render(<InlineDateField value={null} label="Date réalisée" onChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Date réalisée" })).toHaveTextContent(
      "Dater",
    );
  });

  it("shows the date in words rather than in ISO", () => {
    render(
      <InlineDateField value="2026-11-30" label="Date estimée" onChange={vi.fn()} />,
    );

    expect(screen.getByText("30 nov. 2026")).toBeInTheDocument();
  });

  it("posts the date typed", async () => {
    const onChange = vi.fn();
    render(<InlineDateField value={null} label="Date estimée" onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: "Date estimée" }));
    await userEvent.type(screen.getByLabelText("Date estimée"), "2026-11-30");
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith("2026-11-30");
  });

  it("does not write back what was already there", async () => {
    const onChange = vi.fn();
    render(
      <InlineDateField value="2026-11-30" label="Date estimée" onChange={onChange} />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Date estimée" }));
    await userEvent.tab();

    expect(onChange).not.toHaveBeenCalled();
  });

  it("clears a date that may be cleared", async () => {
    const onChange = vi.fn();
    render(
      <InlineDateField
        value="2026-11-30"
        label="Date réalisée"
        clearable
        onChange={onChange}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Retirer Date réalisée" }),
    );

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("offers no way to clear a date the row cannot do without", () => {
    render(
      <InlineDateField value="2026-11-30" label="Date estimée" onChange={vi.fn()} />,
    );

    expect(screen.queryByRole("button", { name: /Retirer/ })).not.toBeInTheDocument();
  });

  it("reads as plain text where nothing may be written", () => {
    render(
      <InlineDateField
        value="2026-11-30"
        label="Date estimée"
        editable={false}
        onChange={vi.fn()}
      />,
    );

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("30 nov. 2026")).toBeInTheDocument();
  });

  /** Red is not enough on its own: the words carry it for whoever cannot see it. */
  it("says a day gone by in words as well as in colour", () => {
    render(
      <InlineDateField
        value="2026-06-30"
        label="Date estimée"
        late
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByText("en retard")).toBeInTheDocument();
  });
});
