"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { UserRow } from "@/components/molecules/UserRow";
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
 * La liste des collaborateurs.
 *
 * Chacun la consulte : savoir qui compose l'equipe et qui peut rouvrir un mois
 * validé n'est pas un secret de manager. Seul le changement de role l'est.
 */
export function UsersPage() {
  const ecran = useUsersScreen();

  return (
    <main className="p-6">
      <PageHeader
        titre="Utilisateurs"
        soustitre={
          ecran.isManager
            ? "Vous pouvez promouvoir un utilisateur. Chaque changement est tracé."
            : "Consultable par toute l'équipe. Seul un manager change un rôle."
        }
        actions={
          <Button variant="outline" onClick={ecran.basculerInactifs}>
            {ecran.avecInactifs ? "Masquer les inactifs" : "Afficher les inactifs"}
          </Button>
        }
      />

      {/* La liste reste etroite : quatre colonnes etalees sur 2000 px ne se lisent plus. */}
      <div className="max-w-[900px]">
        {ecran.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {!ecran.isLoading && ecran.collaborateurs.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            Aucun utilisateur. Les comptes se créent à la première connexion.
          </p>
        )}

        {ecran.collaborateurs.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Utilisateur</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Rôle</TableHead>
                <TableHead>Dernière connexion</TableHead>
                <TableHead>Statut</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ecran.collaborateurs.map((collaborateur) => (
                <UserRow
                  key={collaborateur.id}
                  user={collaborateur}
                  roleModifiable={ecran.isManager}
                  onChangeRole={ecran.changerRole}
                  maintenant={ecran.maintenant}
                />
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </main>
  );
}
