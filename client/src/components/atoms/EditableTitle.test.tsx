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
  it("shows the title, at the level asked for", () => {
    render(<EditableTitle {...baseProps} niveau={1} />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Portail bailleurs",
    );
  });

  it("opens a pre-filled field on a click on the pencil", async () => {
    render(<EditableTitle {...baseProps} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));

    expect(screen.getByRole("textbox")).toHaveValue("Portail bailleurs");
  });

  it("saves the new title", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "Extranet copropriété");
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onRename).toHaveBeenCalledWith("Extranet copropriété");
  });

  it("saves on the Enter key too", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "Extranet{Enter}");

    expect(onRename).toHaveBeenCalledWith("Extranet");
  });

  it("gives up the input on cancel", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.type(screen.getByRole("textbox"), " bis");
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onRename).not.toHaveBeenCalled();
    expect(screen.getByRole("heading")).toHaveTextContent("Portail bailleurs");
  });

  it("gives up on the Escape key too", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.type(screen.getByRole("textbox"), "{Escape}");

    expect(onRename).not.toHaveBeenCalled();
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });

  it("writes nothing when the title has not changed", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onRename).not.toHaveBeenCalled();
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });

  it("refuses an empty title", async () => {
    const onRename = vi.fn();
    render(<EditableTitle {...baseProps} onRename={onRename} />);

    await userEvent.click(screen.getByRole("button", { name: "Renommer la mission" }));
    await userEvent.clear(screen.getByRole("textbox"));

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeDisabled();
  });

  it("keeps the input and warns when saving fails", async () => {
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

  it("does not offer the pencil when renaming is not allowed", () => {
    render(<EditableTitle {...baseProps} onRename={undefined} />);

    expect(
      screen.queryByRole("button", { name: "Renommer la mission" }),
    ).not.toBeInTheDocument();
  });
});
