import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SearchField } from "./SearchField";

describe("SearchField", () => {
  it("names the field the same way to the eye and to a screen reader", () => {
    render(<SearchField value="" onChange={vi.fn()} label="Rechercher un projet" />);

    const field = screen.getByRole("searchbox", { name: "Rechercher un projet" });
    expect(field).toHaveAttribute("placeholder", "Rechercher un projet");
  });

  it("passes on every keystroke, without waiting for a confirmation", () => {
    const onChange = vi.fn();
    render(<SearchField value="" onChange={onChange} label="Rechercher" />);

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "co" } });

    expect(onChange).toHaveBeenCalledWith("co");
  });

  it("shows what is being searched", () => {
    render(<SearchField value="copro" onChange={vi.fn()} label="Rechercher" />);

    expect(screen.getByRole("searchbox")).toHaveValue("copro");
  });
});
