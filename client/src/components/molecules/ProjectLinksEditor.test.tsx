import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ProjectLinksEditor } from "./ProjectLinksEditor";
import type { ProjectLinkResponse } from "@/lib/api/generated/model";

const link = (
  id: number,
  label: string,
  icon: ProjectLinkResponse["icon"] = "link",
): ProjectLinkResponse => ({ id, label, url: `https://waat.fr/${id}`, icon });

function openForm() {
  fireEvent.click(screen.getByRole("button", { name: "Ajouter un lien" }));
}

function enter(placeholder: string, value: string) {
  fireEvent.change(screen.getByPlaceholderText(placeholder), {
    target: { value: value },
  });
}

describe("ProjectLinksEditor", () => {
  it("offers only adding when the mission has no link", () => {
    render(<ProjectLinksEditor links={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ajouter un lien" })).toBeInTheDocument();
  });

  it("keeps the form closed until it is asked for", () => {
    render(<ProjectLinksEditor links={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    expect(screen.queryByPlaceholderText("https://…")).not.toBeInTheDocument();
  });

  it("lists every link of the mission", () => {
    render(
      <ProjectLinksEditor
        links={[link(1, "Le dépôt", "repository"), link(2, "Maquettes", "design")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByRole("link", { name: /Le dépôt/ })).toHaveAttribute(
      "href",
      "https://waat.fr/1",
    );
    expect(screen.getByRole("link", { name: /Maquettes/ })).toBeInTheDocument();
  });

  it("annonce l'icône de chaque lien", () => {
    render(
      <ProjectLinksEditor
        links={[link(1, "Le dépôt", "repository")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Dépôt de code")).toBeInTheDocument();
  });

  it("lets the address decide the default icon", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    openForm();
    enter("Intitulé (facultatif)", "Le dépôt");
    enter("https://…", "https://github.com/waat/x");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() =>
      expect(onAdd).toHaveBeenCalledWith("Le dépôt", "https://github.com/waat/x", null),
    );
  });

  it("passes on the icon chosen by hand", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    openForm();
    fireEvent.click(screen.getByRole("button", { name: "Choisir l'icône du lien" }));
    fireEvent.click(screen.getByRole("button", { name: /Tableur/ }));
    enter("https://…", "https://waat.fr/budget");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() =>
      expect(onAdd).toHaveBeenCalledWith("", "https://waat.fr/budget", "spreadsheet"),
    );
  });

  it("refuses to add until an address is typed", () => {
    render(<ProjectLinksEditor links={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    openForm();

    expect(screen.getByRole("button", { name: "Ajouter" })).toBeDisabled();
  });

  it("explains an address the server refused", async () => {
    const onAdd = vi.fn().mockRejectedValue(new Error("400"));
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    openForm();
    enter("https://…", "ftp://waat.fr");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    expect(await screen.findByText(/n'est pas valide/)).toBeInTheDocument();
  });

  it("starts from a blank form after an add", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    openForm();
    enter("https://…", "https://waat.fr/x");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() => expect(onAdd).toHaveBeenCalled());
    openForm();
    expect(screen.getByPlaceholderText("https://…")).toHaveValue("");
  });

  it("detaches a link", () => {
    const onRemove = vi.fn().mockResolvedValue(undefined);
    render(
      <ProjectLinksEditor
        links={[link(7, "Maquettes", "design")]}
        onAdd={vi.fn()}
        onRemove={onRemove}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retirer Maquettes" }));

    expect(onRemove).toHaveBeenCalledWith(7);
  });

  it("offers removal of each link without waiting for a hover", () => {
    // The cross must not have to be earned: on a touch screen there is no hover.
    render(
      <ProjectLinksEditor
        links={[link(1, "Le dépôt", "repository"), link(2, "Maquettes", "design")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Retirer Le dépôt" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Retirer Maquettes" })).toBeVisible();
  });
});
