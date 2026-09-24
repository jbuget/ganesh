"use client";

import { UserPlus } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { DeclareUserDialog } from "@/components/molecules/DeclareUserDialog";
import { UserFilters } from "@/components/molecules/UserFilters";
import { PageLayout } from "@/components/organisms/PageLayout";
import { UserPanel } from "@/components/organisms/UserPanel";
import { UsersTable } from "@/components/organisms/UsersTable";
import { Button } from "@/components/ui/button";
import { useOpenedUser } from "@/lib/opened-user";
import { grantableBy, mayActOn } from "@/lib/roles";
import { useUserFilters } from "@/lib/use-user-filters";
import { withGuests } from "@/lib/user-filters";
import { useUserSort } from "@/lib/use-user-sort";
import { useUsersScreen } from "@/lib/use-users";

/**
 * The list of teammates.
 *
 * Anyone may look at it: knowing who makes up the team and who can reopen a
 * validated month is no manager's secret. Only changing a role is.
 *
 * The list compares; the panel holds one teammate. A row therefore opens the
 * panel, which is the only place a role or an access is given away.
 *
 * The page holds the question — the criteria, the order, what to say when
 * nothing comes back — and hands the answer to the table.
 */
export function UsersPage() {
  // Criteria and order live in the address, as on the mission reference list:
  // a list searched and arranged a certain way is shared by a link, and
  // survives a reload.
  const { filters, hasFilter, set, clear } = useUserFilters();
  const { sorted, toggle: sortBy } = useUserSort();
  const screen = useUsersScreen(filters, sorted);
  const panel = useOpenedUser();
  const opened = panel.openedUser ? screen.find(panel.openedUser) : null;
  const [declaring, setDeclaring] = useState(false);
  // Worked out once, here: the picker and the panel only draw the answer.
  const grantable = grantableBy(screen.me);

  return (
    <PageLayout
      header={
        <>
          <PageHeader
            title="Utilisateurs"
            subtitle={
              screen.isManager
                ? "Qui compose l'équipe, et qui peut quoi. Chaque changement est tracé."
                : "Qui compose l'équipe, et qui peut quoi. Seul un manager change un rôle."
            }
            actions={
              screen.isManager ? (
                <Button className="cursor-pointer" onClick={() => setDeclaring(true)}>
                  <UserPlus className="size-4" aria-hidden />
                  Déclarer un utilisateur
                </Button>
              ) : undefined
            }
          />

          {/* With the header, outside the scrolling area: the question asked of
              the list must stay readable and editable, whether one has gone
              thirty rows down or not. Deactivated accounts are one of the
              criteria — « Statut » — and no longer a switch of their own. */}
          <UserFilters
            filters={filters}
            hasFilter={hasFilter}
            onChange={set}
            onClear={clear}
            visible={screen.visible}
            total={screen.total}
            hidden={screen.hidden}
            onShowGuests={() => set(withGuests(filters))}
          />
        </>
      }
    >
      {/* The list stays narrow: columns spread over 2000 px stop being readable. */}
      <div className="max-w-[1050px]">
        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {/* An empty list is answered here and not by the table: the reason is
            the page's — a filter that keeps nobody, or a team yet to sign in. */}
        {!screen.isLoading && screen.users.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            {hasFilter
              ? "Aucun collaborateur ne répond aux filtres."
              : "Aucun utilisateur. Un compte naît d'une déclaration, ou de la première connexion de son titulaire."}
          </p>
        )}

        {screen.users.length > 0 && (
          <UsersTable
            users={screen.users}
            sorted={sorted}
            onSort={sortBy}
            now={screen.now}
            onOpen={panel.open}
          />
        )}
      </div>

      {screen.isManager && (
        <DeclareUserDialog
          open={declaring}
          onOpenChange={setDeclaring}
          grantable={grantable}
          onConfirm={screen.declare}
        />
      )}

      {opened && (
        <UserPanel
          user={opened}
          // Nobody moves their own rank, nor one standing above their own.
          roleModifiable={mayActOn(screen.me, opened)}
          grantable={grantable}
          canChangeStatus={mayActOn(screen.me, opened)}
          editable={screen.isManager}
          onChangeRole={screen.changeRole}
          onSetActive={screen.setActive}
          onUpdateIdentity={screen.updateIdentity}
          now={screen.now}
          onClose={panel.close}
        />
      )}
    </PageLayout>
  );
}
