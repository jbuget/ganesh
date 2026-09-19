import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RangeTabs } from "./RangeTabs";

describe("RangeTabs", () => {
  it("offers every window", () => {
    render(<RangeTabs value="last_30_days" onChange={vi.fn()} />);

    expect(screen.getAllByRole("tab")).toHaveLength(5);
  });

  it("marks the window being read", () => {
    render(<RangeTabs value="last_30_days" onChange={vi.fn()} />);

    expect(screen.getByRole("tab", { name: "30 derniers jours" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: "Hier" })).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  it("changes window on a click", async () => {
    const onChange = vi.fn();
    render(<RangeTabs value="last_30_days" onChange={onChange} />);

    await userEvent.click(screen.getByRole("tab", { name: "7 derniers jours" }));

    expect(onChange).toHaveBeenCalledWith("last_7_days");
  });

  it("does not ask again for the window already shown", async () => {
    const onChange = vi.fn();
    render(<RangeTabs value="today" onChange={onChange} />);

    await userEvent.click(screen.getByRole("tab", { name: "Aujourd'hui" }));

    expect(onChange).not.toHaveBeenCalled();
  });
});
