"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { PageLayout } from "@/components/organisms/PageLayout";
import { UserPanel } from "@/components/organisms/UserPanel";
import { UsersTable } from "@/components/organisms/UsersTable";
import { Button } from "@/components/ui/button";
import { useOpenedUser } from "@/lib/opened-user";
import { useUsersScreen } from "@/lib/use-users";

/**
 * The list of teammates.
 *
 * Anyone may look at it: knowing who makes up the team and who can reopen a
 * validated month is no manager's secret. Only changing a role is.
 *
 * The list compares; the panel holds one teammate. A row therefore opens the
 * panel, which is the only place a role or an access is given away.
 */
export function UsersPage() {
  const screen = useUsersScreen();
  const panel = useOpenedUser();
  const opened = panel.openedUser ? screen.find(panel.openedUser) : null;

  return (
    <PageLayout
      header={
        <PageHeader
          title="Utilisateurs"
          subtitle={
            screen.isManager
              ? "Vous pouvez promouvoir un utilisateur. Chaque changement est tracé."
              : "Consultable par toute l'équipe. Seul un manager change un rôle."
          }
          actions={
            <Button variant="outline" onClick={screen.toggleInactive}>
              {screen.withInactive ? "Masquer les inactifs" : "Afficher les inactifs"}
            </Button>
          }
        />
      }
    >
      {/* The list stays narrow: columns spread over 2000 px stop being readable. */}
      <div className="max-w-[1050px]">
        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {!screen.isLoading && screen.users.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            Aucun utilisateur. Les comptes se créent à la première connexion.
          </p>
        )}

        {screen.users.length > 0 && (
          <UsersTable users={screen.users} now={screen.now} onOpen={panel.open} />
        )}
      </div>

      {opened && (
        <UserPanel
          user={opened}
          roleModifiable={screen.isManager}
          canChangeStatus={screen.isManager && opened.id !== screen.meId}
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
