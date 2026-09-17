import { beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Table, TableBody } from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";

import { UserRow } from "./UserRow";

const jeremy: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initiales: "JB",
  role: "MANAGER",
  actif: true,
};

const MAINTENANT = new Date("2026-09-17T12:00:00");

const onSetActive = vi.fn();

function renderRow(
  user: UserResponse,
  roleModifiable = false,
  statutModifiable = false,
) {
  return render(
    <Table>
      <TableBody>
        <UserRow
          user={user}
          roleModifiable={roleModifiable}
          statutModifiable={statutModifiable}
          onChangeRole={vi.fn()}
          onSetActive={onSetActive}
          maintenant={MAINTENANT}
        />
      </TableBody>
    </Table>,
  );
}

describe("UserRow", () => {
  beforeEach(() => onSetActive.mockClear());

  it("affiche le collaborateur, son email et son rôle", () => {
    renderRow(jeremy);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("j.buget@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("nomme le statut dans les deux cas", () => {
    renderRow(jeremy);
    expect(screen.getByText("Actif")).toBeInTheDocument();

    cleanup();
    renderRow({ ...jeremy, actif: false });
    expect(screen.getByText("Désactivé")).toBeInTheDocument();
  });

  it("n'offre pas de couper un accès sans droit de gestion", () => {
    renderRow(jeremy, false, false);

    expect(screen.queryByRole("button", { name: /Désactiver/ })).toBeNull();
  });

  it("demande confirmation avant de couper un accès", async () => {
    renderRow(jeremy, true, true);

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));

    // Couper l'acces ne part pas sur un simple clic.
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(onSetActive).not.toHaveBeenCalled();
  });

  it("coupe l'accès une fois la confirmation donnée", async () => {
    renderRow(jeremy, true, true);

    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));
    // Le bouton du dialogue, pas la pastille qui l'a ouvert.
    await userEvent.click(screen.getByRole("button", { name: /^Désactiver$/ }));

    expect(onSetActive).toHaveBeenCalledWith(1, false);
  });

  it("rétablit un accès sans confirmation, car cela ne retire rien", async () => {
    renderRow({ ...jeremy, actif: false }, true, true);

    await userEvent.click(screen.getByRole("button", { name: "Réactiver ce compte" }));

    expect(onSetActive).toHaveBeenCalledWith(1, true);
  });

  it("laisse un manager changer le rôle", () => {
    renderRow(jeremy, true);

    expect(screen.getByRole("button", { name: /Changer le rôle/ })).toBeInTheDocument();
  });

  it("n'offre pas de changer le rôle sans droit de gestion", () => {
    renderRow(jeremy, false);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });

  it("dit depuis quand le compte ne s'est plus connecté", () => {
    renderRow({ ...jeremy, derniere_connexion: "2026-09-17T09:00:00" });

    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
  });

  it("distingue un compte qui ne s'est jamais connecté", () => {
    renderRow({ ...jeremy, derniere_connexion: null });

    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });
});
