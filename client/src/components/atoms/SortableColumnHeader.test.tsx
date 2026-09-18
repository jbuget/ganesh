import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SortableColumnHeader } from "./SortableColumnHeader";
import { NO_SORT, type MissionSort } from "@/lib/mission-sort";

function show(sorted: MissionSort, onToggle = vi.fn()) {
  render(
    <table>
      <thead>
        <tr>
          <SortableColumnHeader
            column="estimated"
            label="Estimé"
            sorted={sorted}
            onToggle={onToggle}
          />
        </tr>
      </thead>
    </table>,
  );
  return onToggle;
}

describe("SortableColumnHeader", () => {
  it("asks for ordering by its column when clicked", () => {
    const onToggle = show(NO_SORT);

    fireEvent.click(screen.getByRole("button", { name: /Estimé/ }));

    expect(onToggle).toHaveBeenCalledWith("estimated");
  });

  it("announces no order while the column does not order the list", () => {
    show(NO_SORT);

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });

  it("shows the ascending direction when it orders the list", () => {
    show({ column: "estimated", direction: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "ascending");
    expect(screen.getByLabelText("Ordre croissant")).toBeInTheDocument();
  });

  it("shows the descending direction", () => {
    show({ column: "estimated", direction: "desc" });

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
