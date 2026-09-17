import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

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

function renderRow(user: UserResponse, roleModifiable = false) {
  return render(
    <Table>
      <TableBody>
        <UserRow user={user} roleModifiable={roleModifiable} onChangeRole={vi.fn()} />
      </TableBody>
    </Table>,
  );
}

describe("UserRow", () => {
  it("affiche le collaborateur, son email et son rôle", () => {
    renderRow(jeremy);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("j.buget@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("signale un collaborateur désactivé", () => {
    renderRow({ ...jeremy, actif: false });

    expect(screen.getByText("Inactif")).toBeInTheDocument();
  });

  it("ne signale rien pour un collaborateur actif", () => {
    renderRow(jeremy);

    expect(screen.queryByText("Inactif")).toBeNull();
  });

  it("laisse un manager changer le rôle", () => {
    renderRow(jeremy, true);

    expect(screen.getByRole("button", { name: /Changer le rôle/ })).toBeInTheDocument();
  });

  it("n'offre pas de changer le rôle sans droit de gestion", () => {
    renderRow(jeremy, false);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
  });
});
