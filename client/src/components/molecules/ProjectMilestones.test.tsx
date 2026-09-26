import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectMilestones } from "./ProjectMilestones";
import type { MilestoneResponse } from "@/lib/api/generated/model";

const TODAY = new Date("2026-09-25T10:00:00");

function aMilestone(overrides: Partial<MilestoneResponse> = {}): MilestoneResponse {
  return {
    id: 1,
    project_id: 10,
    label: "Livraison du lot 1",
    expected_on: "2026-11-30",
    reached_on: null,
    ...overrides,
  };
}

function renderThem(
  milestones: MilestoneResponse[],
  props: Partial<Parameters<typeof ProjectMilestones>[0]> = {},
) {
  return render(
    <ProjectMilestones
      milestones={milestones}
      now={TODAY}
      editable
      onAdd={vi.fn()}
      onChange={vi.fn()}
      onRemove={vi.fn()}
      {...props}
    />,
  );
}

describe("ProjectMilestones", () => {
  it("says plainly that a mission carries no date", () => {
    renderThem([]);

    expect(screen.getByText(/Aucun jalon/)).toBeInTheDocument();
  });

  it("names each milestone and shows the day it is expected", () => {
    renderThem([aMilestone()]);

    expect(screen.getByDisplayValue).toBeDefined();
    expect(screen.getByRole("button", { name: /Nom du jalon/ })).toHaveTextContent(
      "Livraison du lot 1",
    );
    expect(screen.getByText("30 nov. 2026")).toBeInTheDocument();
  });

  /** Which date is which: two columns of dates read as one without this. */
  it("names both columns of dates", () => {
    renderThem([aMilestone()]);

    expect(screen.getByText("Date estimée")).toBeInTheDocument();
    expect(screen.getByText("Date réalisée")).toBeInTheDocument();
  });

  it("marks a day gone by with nothing reached as late", () => {
    renderThem([aMilestone({ expected_on: "2026-06-30" })]);

    expect(screen.getByText("en retard")).toBeInTheDocument();
  });

  it("records a milestone reached after the day it was expected", async () => {
    const onChange = vi.fn();
    renderThem([aMilestone({ expected_on: "2026-06-30" })], { onChange });

    await userEvent.click(
      screen.getByRole("button", { name: /Date réalisée de Livraison du lot 1/ }),
    );
    await userEvent.type(
      screen.getByLabelText(/Date réalisée de Livraison du lot 1/),
      "2026-09-20",
    );
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith(1, { reached_on: "2026-09-20" });
  });

  it("never calls a milestone that happened late", () => {
    renderThem([aMilestone({ expected_on: "2026-06-30", reached_on: "2026-07-15" })]);

    expect(screen.queryByText("en retard")).not.toBeInTheDocument();
  });

  it("posts the day a milestone was reached", async () => {
    const onChange = vi.fn();
    renderThem([aMilestone()], { onChange });

    await userEvent.click(
      screen.getByRole("button", { name: /Date réalisée de Livraison du lot 1/ }),
    );
    await userEvent.type(
      screen.getByLabelText(/Date réalisée de Livraison du lot 1/),
      "2026-09-20",
    );
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith(1, { reached_on: "2026-09-20" });
  });

  it("moves the day a milestone is announced for", async () => {
    const onChange = vi.fn();
    renderThem([aMilestone()], { onChange });

    await userEvent.click(
      screen.getByRole("button", { name: /Date estimée de Livraison du lot 1/ }),
    );
    const field = screen.getByLabelText(/Date estimée de Livraison du lot 1/);
    await userEvent.clear(field);
    await userEvent.type(field, "2026-12-15");
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith(1, { expected_on: "2026-12-15" });
  });

  /** A date posted by mistake simply leaves: nothing is booked against one. */
  it("withdraws a milestone", async () => {
    const onRemove = vi.fn();
    renderThem([aMilestone()], { onRemove });

    await userEvent.click(
      screen.getByRole("button", { name: /Retirer Livraison du lot 1/ }),
    );

    expect(onRemove).toHaveBeenCalledWith(1);
  });

  it("posts a new milestone with the name and the day it was given", async () => {
    const onAdd = vi.fn();
    renderThem([], { onAdd });

    await userEvent.type(screen.getByLabelText("Nom du jalon à ajouter"), "Recette");
    await userEvent.type(screen.getByLabelText("Date estimée du jalon"), "2026-10-15");
    await userEvent.click(screen.getByRole("button", { name: "Ajouter le jalon" }));

    expect(onAdd).toHaveBeenCalledWith("Recette", "2026-10-15");
  });

  /** Both are required: the domain refuses the rest, and so does the form. */
  it("refuses to post a milestone with no name", async () => {
    const onAdd = vi.fn();
    renderThem([], { onAdd });

    await userEvent.type(screen.getByLabelText("Date estimée du jalon"), "2026-10-15");
    await userEvent.click(screen.getByRole("button", { name: "Ajouter le jalon" }));

    expect(onAdd).not.toHaveBeenCalled();
  });

  it("refuses to post a milestone with no day", async () => {
    const onAdd = vi.fn();
    renderThem([], { onAdd });

    await userEvent.type(screen.getByLabelText("Nom du jalon à ajouter"), "Recette");
    await userEvent.click(screen.getByRole("button", { name: "Ajouter le jalon" }));

    expect(onAdd).not.toHaveBeenCalled();
  });

  it("offers no gesture to whoever may only read", () => {
    renderThem([aMilestone()], { editable: false });

    expect(screen.queryByLabelText("Nom du jalon à ajouter")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Retirer/ })).not.toBeInTheDocument();
    expect(screen.getByText("Livraison du lot 1")).toBeInTheDocument();
  });
});
