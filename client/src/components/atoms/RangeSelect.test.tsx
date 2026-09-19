import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RangeSelect } from "./RangeSelect";

async function open() {
  await userEvent.click(screen.getByRole("button", { name: /Plage de temps/ }));
}

describe("RangeSelect", () => {
  it("announces the window being read, folded", () => {
    render(<RangeSelect value="last_30_days" onChange={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("30 derniers jours");
  });

  it("keeps the menu closed until it is asked for", () => {
    render(<RangeSelect value="last_30_days" onChange={vi.fn()} />);

    expect(screen.queryByRole("option")).not.toBeInTheDocument();
  });

  it("offers every window once open", async () => {
    render(<RangeSelect value="last_30_days" onChange={vi.fn()} />);

    await open();

    expect(screen.getAllByRole("option")).toHaveLength(5);
  });

  it("marks the window being read", async () => {
    render(<RangeSelect value="last_30_days" onChange={vi.fn()} />);

    await open();

    expect(screen.getByRole("option", { name: /30 derniers jours/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("option", { name: /Hier/ })).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  it("changes window on a choice", async () => {
    const onChange = vi.fn();
    render(<RangeSelect value="last_30_days" onChange={onChange} />);

    await open();
    await userEvent.click(screen.getByRole("option", { name: /7 derniers jours/ }));

    expect(onChange).toHaveBeenCalledWith("last_7_days");
  });

  it("closes once a window is chosen", async () => {
    render(<RangeSelect value="last_30_days" onChange={vi.fn()} />);

    await open();
    await userEvent.click(screen.getByRole("option", { name: /7 derniers jours/ }));

    expect(screen.queryByRole("option")).not.toBeInTheDocument();
  });

  it("does not ask again for the window already shown", async () => {
    const onChange = vi.fn();
    render(<RangeSelect value="today" onChange={onChange} />);

    await open();
    await userEvent.click(screen.getByRole("option", { name: /Aujourd'hui/ }));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("keeps its width whichever window is in force", async () => {
    // jsdom lays nothing out, so the guarantee is checked where it is
    // declared: a fixed width, identical from one window to the next. Without
    // it the control shrinks on « Hier » and grows on « 90 derniers jours »,
    // and the header jumps at every change.
    const { rerender } = render(<RangeSelect value="today" onChange={vi.fn()} />);
    const shortest = screen.getByRole("button").className;

    rerender(<RangeSelect value="last_90_days" onChange={vi.fn()} />);

    expect(screen.getByRole("button").className).toBe(shortest);
    expect(shortest).toMatch(/\bw-\d/);
  });

  it("keeps the menu as wide as the control that opens it", async () => {
    render(<RangeSelect value="today" onChange={vi.fn()} />);
    const width = screen.getByRole("button").className.match(/\bw-\d+/)?.[0];

    await open();

    expect(screen.getByRole("listbox").parentElement?.className).toContain(width);
  });

  it("names what it selects, for a screen reader", () => {
    render(<RangeSelect value="today" onChange={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Plage de temps, actuellement Aujourd'hui" }),
    ).toBeInTheDocument();
  });
});
