"use client";

import { Plus, Upload } from "lucide-react";
import { Fragment, useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { ImportProjectsDialog } from "@/components/atoms/ImportProjectsDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { MissionRow } from "@/components/molecules/MissionRow";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useMissionOuverte } from "@/lib/mission-ouverte";
import { useProjectsScreen } from "@/lib/use-projects";

/**
 * Le referentiel des missions.
 *
 * Les colonnes disent d'un coup d'oeil ou en est chaque mission, ce qu'elle
 * pese et qui s'en occupe — ce qu'on vient comparer ici. Elles ne s'editent
 * pas : la ligne n'ouvre toujours qu'une chose, le panneau de la mission,
 * celui-la meme que le kanban. Une liste qui editerait en place multiplierait
 * les chemins vers la meme donnee, et les ferait diverger.
 */
export function ProjectsPage() {
  const ecran = useProjectsScreen();
  const panneau = useMissionOuverte();
  const [declaration, setDeclaration] = useState(false);
  const [importation, setImportation] = useState(false);

  return (
    <PageLayout
      entete={
        <PageHeader
          titre="Référentiel des missions"
          soustitre="Ouvert à toute l'équipe. Chaque modification est tracée."
          actions={
            <>
              {ecran.isManager && (
                <Button variant="outline" onClick={() => setImportation(true)}>
                  <Upload />
                  Importer
                </Button>
              )}
              <Button onClick={() => setDeclaration(true)}>
                <Plus />
                Déclarer un projet
              </Button>
            </>
          }
        />
      }
    >
      {/* Assez large pour huit colonnes, pas au point d'etirer les noms. */}
      <div className="max-w-[1200px]">
        {ecran.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {ecran.arbre.length === 0 && !ecran.isLoading && (
          <p className="py-8 text-center text-sm text-slate-500">
            Aucun projet. Déclarez-en un ou importez votre référentiel.
          </p>
        )}

        {ecran.arbre.length > 0 && (
          // Le conteneur de shadcn ouvre un contexte de defilement qui
          // retiendrait l'en-tete a l'interieur du tableau : on le neutralise
          // pour que le `sticky` se cale sur la zone defilante de la page.
          <div className="[&_[data-slot=table-container]]:overflow-visible">
            <Table>
              {/* Soixante lignes passent sous l'en-tete : sans lui, on ne sait
                  plus quelle colonne on lit arrive en bas. Le fond se pose sur
                  les cellules et non sur la rangee : dans un tableau, celui de
                  la rangee se peint sous les lignes qui defilent. */}
              <TableHeader className="sticky top-0 z-10 [&_th]:border-b [&_th]:border-slate-200 [&_th]:bg-slate-50">
                <TableRow>
                  <TableHead>Mission</TableHead>
                  {/* Le fil de suivi : son icone porte le sens, pas un titre. */}
                  <TableHead />
                  <TableHead>Phase</TableHead>
                  <TableHead>Catégorie</TableHead>
                  <TableHead className="text-right">Estimé</TableHead>
                  <TableHead className="text-right">Réalisé</TableHead>
                  <TableHead>Référents</TableHead>
                  <TableHead>Intervenants</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {ecran.arbre.map(({ mission, lots }) => (
                  <Fragment key={mission.project.id}>
                    <MissionRow
                      mission={mission}
                      estLot={mission.project.kind === "lot"}
                      onOpen={() => panneau.ouvrir(mission.project.id)}
                    />
                    {lots.map((lot) => (
                      <MissionRow
                        key={lot.project.id}
                        mission={lot}
                        estLot
                        onOpen={() => panneau.ouvrir(lot.project.id)}
                      />
                    ))}
                  </Fragment>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {ecran.activites.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-2 text-sm font-medium text-slate-600">
              Activités hors projet
            </h2>
            <p className="mb-3 text-sm text-slate-500">
              Elles n&apos;ont ni phase ni estimé, et ne remontent jamais dans Monday.
              Sans elles, les jours ouvrés se reporteraient sur les projets.
            </p>
            <ul className="flex flex-wrap gap-2">
              {ecran.activites.map((activite) => (
                <li
                  key={activite.project.id}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
                >
                  {activite.project.label}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <DeclareProjectDialog
        open={declaration}
        onOpenChange={setDeclaration}
        onConfirm={async (label) => {
          await ecran.declare(label, "projet");
        }}
      />

      <ImportProjectsDialog
        open={importation}
        onOpenChange={setImportation}
        onImport={ecran.importCsv}
      />

      {panneau.missionOuverte && (
        <ProjectPanel
          key={panneau.missionOuverte}
          projectId={panneau.missionOuverte}
          onClose={panneau.fermer}
          onMissionChanged={ecran.refresh}
        />
      )}
    </PageLayout>
  );
}
