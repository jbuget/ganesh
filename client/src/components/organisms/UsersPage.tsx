"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { UserRow } from "@/components/molecules/UserRow";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useUsersScreen } from "@/lib/use-users";

/**
 * The list of teammates.
 *
 * Anyone may look at it: knowing who makes up the team and who can reopen a
 * validated month is no manager's secret. Only changing a role is.
 */
export function UsersPage() {
  const screen = useUsersScreen();

  return (
    <PageLayout
      entete={
        <PageHeader
          titre="Utilisateurs"
          soustitre={
            screen.isManager
              ? "Vous pouvez promouvoir un utilisateur. Chaque changement est tracé."
              : "Consultable par toute l'équipe. Seul un manager change un rôle."
          }
          actions={
            <Button variant="outline" onClick={screen.basculerInactifs}>
              {screen.avecInactifs ? "Masquer les inactifs" : "Afficher les inactifs"}
            </Button>
          }
        />
      }
    >
      {/* The list stays narrow: four columns spread over 2000 px stop being readable. */}
      <div className="max-w-[900px]">
        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {!screen.isLoading && screen.collaborateurs.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            Aucun user. Les comptes se créent à la première connexion.
          </p>
        )}

        {screen.collaborateurs.length > 0 && (
          // The same setting as the reference list: the shadcn container opens
          // a scrolling context that would hold the header inside the table,
          // and the background sits on the cells, not on the row.
          <div className="[&_[data-slot=table-container]]:overflow-visible">
            <Table>
              <TableHeader className="sticky top-0 z-10 [&_th]:border-b [&_th]:border-slate-200 [&_th]:bg-slate-50">
                <TableRow>
                  <TableHead>Collaborateur</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Rôle</TableHead>
                  <TableHead>Dernière connexion</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {screen.collaborateurs.map((collaborateur) => (
                  <UserRow
                    key={collaborateur.id}
                    user={collaborateur}
                    roleModifiable={screen.isManager}
                    statutModifiable={
                      screen.isManager && collaborateur.id !== screen.moiId
                    }
                    onChangeRole={screen.changerRole}
                    onSetActive={screen.changerActivite}
                    maintenant={screen.maintenant}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </PageLayout>
  );
}
