import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NO_HIDDEN_COLUMN, hiddenColumns } from "@/lib/mission-columns";

import { ColumnsSelect } from "./ColumnsSelect";

function selector(hidden = NO_HIDDEN_COLUMN) {
  const onToggle = vi.fn();
  const onShowAll = vi.fn();
  render(<ColumnsSelect hidden={hidden} onToggle={onToggle} onShowAll={onShowAll} />);
  return { onToggle, onShowAll };
}

const open = () => userEvent.click(screen.getByRole("button", { name: /Colonnes/ }));

describe("ColumnsSelect", () => {
  it("lists every column one may put away", async () => {
    selector();
    await open();

    for (const column of [
      "Phase",
      "Priorité",
      "Catégorie",
      "Build",
      "Run",
      "Référents",
      "Intervenants",
      "Liens",
    ]) {
      expect(screen.getByRole("button", { name: column })).toBeInTheDocument();
    }
  });

  it("ticks the columns that show", async () => {
    selector(hiddenColumns(["category"]));
    await open();

    expect(screen.getByRole("button", { name: "Phase" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Catégorie" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("asks to put away the column clicked", async () => {
    const { onToggle } = selector();
    await open();

    await userEvent.click(screen.getByRole("button", { name: "Catégorie" }));

    expect(onToggle).toHaveBeenCalledWith("category");
  });

  /** Three columns go away one after the other: the menu must not close. */
  it("stays open from one choice to the next", async () => {
    selector();
    await open();

    await userEvent.click(screen.getByRole("button", { name: "Catégorie" }));

    expect(screen.getByRole("button", { name: "Priorité" })).toBeInTheDocument();
  });

  it("says how many columns are put away, so the folded bar still tells", () => {
    selector(hiddenColumns(["category", "links"]));

    expect(screen.getByRole("button", { name: /Colonnes/ })).toHaveTextContent("2");
  });

  it("brings the whole panorama back at once", async () => {
    const { onShowAll } = selector(hiddenColumns(["category"]));
    await open();

    await userEvent.click(screen.getByRole("button", { name: "Tout afficher" }));

    expect(onShowAll).toHaveBeenCalled();
  });

  it("offers nothing to restore when the panorama is already whole", async () => {
    selector();
    await open();

    expect(screen.queryByRole("button", { name: "Tout afficher" })).toBeNull();
  });
});
