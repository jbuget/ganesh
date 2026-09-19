import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ClearFilters } from "./ClearFilters";

describe("ClearFilters", () => {
  it("puts every criterion back to nothing in one gesture", async () => {
    const onClear = vi.fn();
    render(<ClearFilters onClear={onClear} />);

    await userEvent.click(screen.getByRole("button", { name: /Effacer/ }));

    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
