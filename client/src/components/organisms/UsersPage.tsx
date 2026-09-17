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
 * La liste des collaborateurs.
 *
 * Chacun la consulte : savoir qui compose l'equipe et qui peut rouvrir un mois
 * validé n'est pas un secret de manager. Seul le changement de role l'est.
 */
export function UsersPage() {
  const ecran = useUsersScreen();

  return (
    <PageLayout
      entete={
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
      }
    >
      {/* La liste reste etroite : quatre colonnes etalees sur 2000 px ne se lisent plus. */}
      <div className="max-w-[900px]">
        {ecran.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {!ecran.isLoading && ecran.collaborateurs.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            Aucun utilisateur. Les comptes se créent à la première connexion.
          </p>
        )}

        {ecran.collaborateurs.length > 0 && (
          // Meme reglage que le referentiel : le conteneur de shadcn ouvre un
          // contexte de defilement qui retiendrait l'en-tete a l'interieur du
          // tableau, et le fond se pose sur les cellules, non sur la rangee.
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
                {ecran.collaborateurs.map((collaborateur) => (
                  <UserRow
                    key={collaborateur.id}
                    user={collaborateur}
                    roleModifiable={ecran.isManager}
                    statutModifiable={
                      ecran.isManager && collaborateur.id !== ecran.moiId
                    }
                    onChangeRole={ecran.changerRole}
                    onSetActive={ecran.changerActivite}
                    maintenant={ecran.maintenant}
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
