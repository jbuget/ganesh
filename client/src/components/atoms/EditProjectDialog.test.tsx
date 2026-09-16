import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { EditProjectDialog } from "./EditProjectDialog";
import type { ProjectResponse } from "@/lib/api/generated/model";

const mission = (over: Partial<ProjectResponse> = {}): ProjectResponse =>
  ({
    id: 1,
    label: "Portail",
    kind: "projet",
    parent_id: null,
    statut: "cadrage",
    actif: true,
    estime_j: 20,
    monday_item_id: null,
    monday_subitem_id: null,
    is_syncable_to_monday: false,
    ...over,
  }) as ProjectResponse;

const baseProps = { onOpenChange: vi.fn(), onConfirm: vi.fn() };

describe("EditProjectDialog", () => {
  it("reste fermé tant qu'aucune mission n'est choisie", () => {
    render(<EditProjectDialog {...baseProps} project={null} />);

    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("pré-remplit les champs avec la mission", () => {
    render(<EditProjectDialog {...baseProps} project={mission()} />);

    expect(screen.getByLabelText("Nom")).toHaveValue("Portail");
    expect(screen.getByLabelText("Estimé (jours)")).toHaveValue(20);
  });

  it("laisse l'estimé vide quand la mission n'en a pas", () => {
    render(<EditProjectDialog {...baseProps} project={mission({ estime_j: null })} />);

    expect(screen.getByLabelText("Estimé (jours)")).toHaveValue(null);
  });

  it("nomme correctement un sous-projet", () => {
    render(<EditProjectDialog {...baseProps} project={mission({ kind: "lot" })} />);

    expect(screen.getByRole("heading")).toHaveTextContent("Modifier le sous-projet");
  });

  it("transmet les valeurs saisies", async () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(
      <EditProjectDialog {...baseProps} onConfirm={onConfirm} project={mission()} />,
    );

    await userEvent.clear(screen.getByLabelText("Nom"));
    await userEvent.type(screen.getByLabelText("Nom"), "Portail bailleurs");
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onConfirm).toHaveBeenCalledWith({
      label: "Portail bailleurs",
      estime_j: 20,
      monday_item_id: null,
    });
  });

  it("refuse d'enregistrer un nom vide", async () => {
    const onConfirm = vi.fn();
    render(
      <EditProjectDialog {...baseProps} onConfirm={onConfirm} project={mission()} />,
    );

    await userEvent.clear(screen.getByLabelText("Nom"));

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeDisabled();
  });

  it("efface l'estimé quand on vide le champ", async () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(
      <EditProjectDialog {...baseProps} onConfirm={onConfirm} project={mission()} />,
    );

    await userEvent.clear(screen.getByLabelText("Estimé (jours)"));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ estime_j: null }));
  });
});
