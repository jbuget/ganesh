import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ApiError } from "@/lib/api/fetcher";
import { TagManagerRow } from "./TagManagerRow";

const SUEZ = { id: 1, name: "Suez", color: "red" as const, project_count: 3 };
const SUEZ_ENV = { id: 2, name: "Suez Env", color: "blue" as const, project_count: 1 };
const FRIGO = { id: 3, name: "Frigo", color: "green" as const, project_count: 1 };

function row(over: Partial<Parameters<typeof TagManagerRow>[0]> = {}) {
  const props = {
    tag: SUEZ_ENV,
    others: [SUEZ, FRIGO],
    onRename: vi.fn().mockResolvedValue(undefined),
    onRecolor: vi.fn().mockResolvedValue(undefined),
    onMerge: vi.fn().mockResolvedValue(undefined),
    ...over,
  };
  render(<TagManagerRow {...props} />);
  return props;
}

describe("TagManagerRow", () => {
  it("names the tag and how many projects carry it", () => {
    row();

    expect(screen.getByText("Suez Env")).toBeInTheDocument();
    expect(screen.getByText("1 projet")).toBeInTheDocument();
  });

  it("pluralises the count", () => {
    row({ tag: SUEZ });

    expect(screen.getByText("3 projets")).toBeInTheDocument();
  });

  it("renames the tag where its name shows", async () => {
    const { onRename } = row();

    await userEvent.click(screen.getByRole("button", { name: "Nom du tag Suez Env" }));
    const field = screen.getByLabelText("Nom du tag Suez Env");
    await userEvent.clear(field);
    await userEvent.type(field, "Suez Group{Enter}");

    expect(onRename).toHaveBeenCalledWith("Suez Group");
  });

  it("refuses a name another tag already carries, and says to fold instead", async () => {
    const { onRename } = row();

    await userEvent.click(screen.getByRole("button", { name: "Nom du tag Suez Env" }));
    const field = screen.getByLabelText("Nom du tag Suez Env");
    await userEvent.clear(field);
    await userEvent.type(field, "suez{Enter}");

    expect(onRename).not.toHaveBeenCalled();
    expect(
      screen.getByText("Un tag porte déjà ce nom : fusionnez-les plutôt."),
    ).toBeInTheDocument();
  });

  it("recolours the tag from the palette", async () => {
    const { onRecolor } = row();

    await userEvent.click(
      screen.getByRole("button", { name: "Couleur du tag Suez Env" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Violet" }));

    expect(onRecolor).toHaveBeenCalledWith("violet");
  });

  it("lists the other tags it could be folded into, never itself", async () => {
    row();

    await userEvent.click(
      screen.getByRole("button", { name: "Fusionner Suez Env dans…" }),
    );

    expect(screen.getByRole("button", { name: /^Suez\b(?! Env)/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Frigo/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Suez Env/ })).not.toBeInTheDocument();
  });

  it("asks to confirm before folding: it cannot be undone", async () => {
    const { onMerge } = row();

    await userEvent.click(
      screen.getByRole("button", { name: "Fusionner Suez Env dans…" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^Suez\b(?! Env)/ }));

    expect(onMerge).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Fusionner « Suez Env » dans « Suez »/),
    ).toBeInTheDocument();
  });

  it("folds the tag once confirmed", async () => {
    const { onMerge } = row();

    await userEvent.click(
      screen.getByRole("button", { name: "Fusionner Suez Env dans…" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^Suez\b(?! Env)/ }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmer la fusion" }));

    expect(onMerge).toHaveBeenCalledWith(1);
  });

  it("gives up on the fold when told to", async () => {
    const { onMerge } = row();

    await userEvent.click(
      screen.getByRole("button", { name: "Fusionner Suez Env dans…" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^Suez\b(?! Env)/ }));
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onMerge).not.toHaveBeenCalled();
    expect(screen.queryByText(/Fusionner « Suez Env »/)).not.toBeInTheDocument();
  });

  it("offers no fold when there is no other tag to fold into", () => {
    row({ others: [] });

    expect(
      screen.queryByRole("button", { name: "Fusionner Suez Env dans…" }),
    ).not.toBeInTheDocument();
  });

  it("says why when the server refuses, in French", async () => {
    const refuses = vi.fn().mockRejectedValue(new ApiError(500, "boom"));
    row({ onRecolor: refuses });

    await userEvent.click(
      screen.getByRole("button", { name: "Couleur du tag Suez Env" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Violet" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ce tag n'a pas pu être enregistré.",
    );
  });
});
