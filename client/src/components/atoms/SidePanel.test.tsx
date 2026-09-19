import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SidePanel } from "./SidePanel";

describe("SidePanel", () => {
  it("names what it holds, so it can be found among the landmarks", () => {
    render(
      <SidePanel label="Jérémy Buget" onClose={vi.fn()}>
        <p>Contenu</p>
      </SidePanel>,
    );

    expect(
      screen.getByRole("complementary", { name: "Jérémy Buget" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Contenu")).toBeInTheDocument();
  });

  it("closes on Escape, so nobody gets stuck in it", async () => {
    const onClose = vi.fn();
    render(
      <SidePanel label="Jérémy Buget" onClose={onClose}>
        <p>Contenu</p>
      </SidePanel>,
    );

    await userEvent.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
