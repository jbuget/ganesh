import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SortableColumnHeader } from "./SortableColumnHeader";
import { NO_SORT, type MissionSort } from "@/lib/mission-sort";

function show(sorted: MissionSort, onToggle = vi.fn()) {
  const view = render(
    <table>
      <thead>
        <tr>
          <SortableColumnHeader
            column="build"
            label="Build"
            sorted={sorted}
            onToggle={onToggle}
          />
        </tr>
      </thead>
    </table>,
  );
  return { onToggle, ...view };
}

/** The lucide class names the drawing: it is the only way to tell them apart. */
const mark = (container: HTMLElement) =>
  [...(container.querySelector("svg")?.classList ?? [])].find((name) =>
    name.startsWith("lucide-"),
  );

describe("SortableColumnHeader", () => {
  it("asks for ordering by its column when clicked", () => {
    const { onToggle } = show(NO_SORT);

    fireEvent.click(screen.getByRole("button", { name: /Build/ }));

    expect(onToggle).toHaveBeenCalledWith("build");
  });

  it("announces no order while the column does not order the list", () => {
    show(NO_SORT);

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });

  it("marks a column one can order by, even while it orders nothing", () => {
    // A sort one has to hover to discover is a sort nobody uses.
    const { container } = show(NO_SORT);

    expect(mark(container)).toBe("lucide-chevrons-up-down");
  });

  it("gives the whole cell to the click, not the title alone", () => {
    show(NO_SORT);

    const target = screen.getByRole("button", { name: /Build/ });
    expect(target.className).toContain("w-full");
    expect(target.className).toContain("h-10");
    expect(screen.getByRole("columnheader").className).toContain("p-0");
  });

  it("shows the ascending direction when it orders the list", () => {
    show({ column: "build", direction: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "ascending");
    expect(screen.getByLabelText("Ordre croissant")).toBeInTheDocument();
  });

  it("shows the descending direction", () => {
    show({ column: "build", direction: "desc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "descending");
    expect(screen.getByLabelText("Ordre décroissant")).toBeInTheDocument();
  });

  it("stays silent when another column orders the list", () => {
    // Two arrows shown at once would no longer say which one orders the list.
    show({ column: "phase", direction: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });
});
