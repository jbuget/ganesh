import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Home, Users } from "lucide-react";
import { describe, expect, it, vi } from "vitest";

import { ScreenVisibilityField } from "./ScreenVisibilityField";
import type { NavBand } from "@/lib/navigation";

const BANDS: NavBand[] = [
  {
    band: "portfolio",
    label: "Portefeuille",
    screens: [{ href: "/projects", label: "Projets", Icon: Home, band: "portfolio" }],
  },
  {
    band: "team",
    label: "Équipe",
    screens: [{ href: "/users", label: "Utilisateurs", Icon: Users, band: "team" }],
  },
];

describe("ScreenVisibilityField", () => {
  it("names each band and lists its screens under it", () => {
    render(<ScreenVisibilityField bands={BANDS} hidden={[]} onChange={vi.fn()} />);

    expect(screen.getByText("Portefeuille")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Projets" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Utilisateurs" })).toBeChecked();
  });

  it("is disabled while a choice is on its way", () => {
    render(
      <ScreenVisibilityField bands={BANDS} hidden={[]} onChange={vi.fn()} isSaving />,
    );

    expect(screen.getByRole("checkbox", { name: "Projets" })).toBeDisabled();
  });

  it("says the whole list when one is ticked off", async () => {
    const onChange = vi.fn();
    render(<ScreenVisibilityField bands={BANDS} hidden={[]} onChange={onChange} />);

    await userEvent.click(screen.getByRole("checkbox", { name: "Projets" }));

    expect(onChange).toHaveBeenCalledWith(["/projects"]);
  });
});
