import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { EditableTitle } from "./EditableTitle";

const baseProps = {
  label: "Portail bailleurs",
  invite: "Renommer la mission",
  onRename: vi.fn(),
};

describe("EditableTitle", () => {
  it("affiche le titre, au niveau demandé", () => {
    render(<EditableTitle {...baseProps} niveau={1} />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Portail bailleurs",
    );
  });

  it("ouvre un champ pré-rempli au clic sur le crayon", async () => {
    render(<EditableTitle {...baseProps} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));

    expect(screen.getByRole("textbox")).toHaveValue("Portail bailleurs");
  });

  it("enregistre le nouveau titre", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "Extranet copropriété");
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onRename).toHaveBeenCalledWith("Extranet copropriété");
  });

  it("enregistre aussi à la touche Entrée", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "Extranet{Enter}");

    expect(onRename).toHaveBeenCalledWith("Extranet");
  });

  it("abandonne la saisie à l'annulation", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.type(screen.getByRole("textbox"), " bis");
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onRename).not.toHaveBeenCalled();
    expect(screen.getByRole("heading")).toHaveTextContent("Portail bailleurs");
  });

  it("abandonne aussi à la touche Échap", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.type(screen.getByRole("textbox"), "{Escape}");

    expect(onRename).not.toHaveBeenCalled();
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });

  it("n'écrit rien quand le titre n'a pas changé", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onRename).not.toHaveBeenCalled();
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });

  it("refuse un titre vide", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeDisabled();
  });

  it("garde la saisie et prévient quand l'enregistrement échoue", async () => {
    const onRename = vi.fn().mockRejectedValue(new Error("boom"));
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "Extranet");
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(screen.getByText(/pas pu être enregistré/)).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("Extranet");
    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeEnabled();
  });

  it("ne propose pas le crayon quand le renommage n'est pas permis", () => {
    render(<EditableTitle {...baseProps} onRename={undefined} />);

    expect(
      screen.queryByRole("button", { name: "Renommer la mission" }),
    ).not.toBeInTheDocument();
  });
});
