import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SimulationBar } from "./SimulationBar";
import type { SimulationResponse } from "@/lib/api/generated/model";

const KEPT: SimulationResponse[] = [
  {
    id: 7,
    name: "Priorité bailleurs",
    horizon_months: 6,
    order: [30, 10],
    staffing: {},
    author_id: 1,
    created_at: "2026-09-19T08:00:00Z",
    updated_at: "2026-09-19T08:00:00Z",
  },
  {
    id: 8,
    name: "Valentin sur le portail",
    horizon_months: 12,
    order: [],
    staffing: { 10: [3] },
    author_id: 1,
    created_at: "2026-09-18T08:00:00Z",
    updated_at: "2026-09-18T08:00:00Z",
  },
];

const NOTHING = {
  onOpen: vi.fn(),
  onSaveAs: vi.fn(async () => true),
  onSaveOver: vi.fn(async () => {}),
  onDelete: vi.fn(),
  onReset: vi.fn(),
};

function draw(props: Partial<Parameters<typeof SimulationBar>[0]> = {}) {
  return render(
    <SimulationBar
      simulations={KEPT}
      opened={null}
      isHypothesis={false}
      hasUnsavedChanges={false}
      saveError={null}
      {...NOTHING}
      {...props}
    />,
  );
}

describe("SimulationBar", () => {
  it("announces the team's own order when no scenario is open", () => {
    draw();

    expect(screen.getByText("Ordre de l'équipe")).toBeInTheDocument();
  });

  it("names the scenario being read", () => {
    draw({ opened: KEPT[0] });

    expect(screen.getByText("Priorité bailleurs")).toBeInTheDocument();
  });

  it("lists what the team kept", async () => {
    draw();

    await userEvent.click(
      screen.getByRole("button", { name: "Choisir une simulation" }),
    );

    expect(screen.getByText("Valentin sur le portail")).toBeInTheDocument();
  });

  it("opens the scenario one picks", async () => {
    const onOpen = vi.fn();
    draw({ onOpen });

    await userEvent.click(
      screen.getByRole("button", { name: "Choisir une simulation" }),
    );
    await userEvent.click(screen.getByText("Valentin sur le portail"));

    expect(onOpen).toHaveBeenCalledWith(KEPT[1]);
  });

  it("offers coming back to the team's order as an entry like the others", async () => {
    // Going back must be as easy as opening a hypothesis, or nobody dares
    // open one.
    const onOpen = vi.fn();
    draw({ opened: KEPT[0], onOpen });

    await userEvent.click(
      screen.getByRole("button", { name: "Choisir une simulation" }),
    );
    await userEvent.click(screen.getByText("Ordre de l'équipe"));

    expect(onOpen).toHaveBeenCalledWith(null);
  });

  it("offers to drop any scenario", async () => {
    const onDelete = vi.fn();
    draw({ onDelete });

    await userEvent.click(
      screen.getByRole("button", { name: "Choisir une simulation" }),
    );
    await userEvent.click(
      screen.getByRole("button", {
        name: "Supprimer la simulation Priorité bailleurs",
      }),
    );

    expect(onDelete).toHaveBeenCalledWith(7);
  });

  it("says so plainly when nothing has been kept yet", async () => {
    draw({ simulations: [] });

    await userEvent.click(
      screen.getByRole("button", { name: "Choisir une simulation" }),
    );

    expect(screen.getByText("Aucune simulation enregistrée.")).toBeInTheDocument();
  });

  it("offers nothing to save while nothing is supposed", () => {
    draw();

    expect(
      screen.queryByRole("button", { name: /Enregistrer/ }),
    ).not.toBeInTheDocument();
  });

  it("offers to keep a hypothesis once there is one", () => {
    draw({ isHypothesis: true });

    expect(
      screen.getByRole("button", { name: "Enregistrer la simulation" }),
    ).toBeInTheDocument();
  });

  it("tells rewriting the open scenario apart from starting a new one", () => {
    // Folding the two into one button would mean guessing which was meant,
    // and guessing wrong silently overwrites somebody else's thinking.
    draw({ opened: KEPT[0], isHypothesis: true, hasUnsavedChanges: true });

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Enregistrer sous…" }),
    ).toBeInTheDocument();
  });

  it("does not offer to rewrite a scenario nothing has changed in", () => {
    draw({ opened: KEPT[0], isHypothesis: true, hasUnsavedChanges: false });

    expect(
      screen.queryByRole("button", { name: "Enregistrer" }),
    ).not.toBeInTheDocument();
  });

  it("names the scenario before keeping it", async () => {
    const onSaveAs = vi.fn(async () => true);
    draw({ isHypothesis: true, onSaveAs });

    await userEvent.click(
      screen.getByRole("button", { name: "Enregistrer la simulation" }),
    );
    await userEvent.type(
      screen.getByLabelText("Nom de la simulation"),
      "Priorité bailleurs",
    );
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onSaveAs).toHaveBeenCalledWith("Priorité bailleurs");
  });

  it("keeps what was typed when the name is refused", async () => {
    // Retyping the whole thing to change one word is a punishment, not a
    // correction.
    const onSaveAs = vi.fn(async () => false);
    draw({
      isHypothesis: true,
      onSaveAs,
      saveError: "Une simulation porte déjà ce nom.",
    });

    await userEvent.click(
      screen.getByRole("button", { name: "Enregistrer la simulation" }),
    );
    await userEvent.type(screen.getByLabelText("Nom de la simulation"), "Doublon");
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(screen.getByLabelText("Nom de la simulation")).toHaveValue("Doublon");
    expect(screen.getByText("Une simulation porte déjà ce nom.")).toBeInTheDocument();
  });
});
