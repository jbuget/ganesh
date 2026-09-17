"use client";

import { Plus, Upload } from "lucide-react";
import { Fragment, useMemo, useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { ImportProjectsDialog } from "@/components/atoms/ImportProjectsDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { SortableColumnHeader } from "@/components/atoms/SortableColumnHeader";
import { MissionFilters } from "@/components/molecules/MissionFilters";
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
import { useOpenedMission } from "@/lib/mission-ouverte";
import { useMissionFilters } from "@/lib/use-mission-filters";
import { useMissionSort } from "@/lib/use-mission-sort";
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
  // Les memes criteres que le kanban, tenus par la meme adresse : on filtre
  // d'un ecran, on ouvre l'autre, et la question posee reste la meme.
  const { filters, hasFilter, set, clear } = useMissionFilters();
  // Le rangement suit le meme chemin que les filtres : l'adresse le porte, et
  // le hook d'ecran rend l'arborescence deja dans l'ordre demande.
  const { sorted, toggle: trierPar } = useMissionSort();
  const screen = useProjectsScreen(filters, sorted);
  // Une seule heure de reference pour toutes les lignes : « il y a 3 h » ne
  // doit pas dependre du moment ou chacune se rend.
  const maintenant = useMemo(() => new Date(), []);
  const panel = useOpenedMission();
  const [declaring, setDeclaration] = useState(false);
  const [importing, setImportation] = useState(false);

  return (
    <PageLayout
      entete={
        <PageHeader
          titre="Projets"
          soustitre="Gestion des projets et sous-projets"
          actions={
            <>
              {screen.isManager && (
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
      {/* Assez large pour neuf colonnes, pas au point d'etirer les noms. */}
      <div className="max-w-[1300px]">
        <MissionFilters
          filters={filters}
          hasFilter={hasFilter}
          onChange={set}
          onEffacer={clear}
          visible={screen.visible}
          total={screen.total}
        />

        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {screen.tree.length === 0 && !screen.isLoading && (
          <p className="py-8 text-center text-sm text-slate-500">
            {hasFilter
              ? "Aucune mission ne répond aux filtres."
              : "Aucun projet. Déclarez-en un ou importez votre référentiel."}
          </p>
        )}

        {screen.tree.length > 0 && (
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
                  <SortableColumnHeader
                    column="project"
                    label="Projet"
                    sorted={sorted}
                    onBasculer={trierPar}
                  />
                  {/* Le fil de suivi : son icone porte le sens, pas un titre. */}
                  <TableHead />
                  <SortableColumnHeader
                    column="phase"
                    label="Phase"
                    sorted={sorted}
                    onBasculer={trierPar}
                  />
                  <SortableColumnHeader
                    column="priority"
                    label="Priorité"
                    sorted={sorted}
                    onBasculer={trierPar}
                  />
                  <SortableColumnHeader
                    column="category"
                    label="Catégorie"
                    sorted={sorted}
                    onBasculer={trierPar}
                  />
                  <SortableColumnHeader
                    column="estimated"
                    label="Estimé"
                    sorted={sorted}
                    onBasculer={trierPar}
                    aDroite
                  />
                  <SortableColumnHeader
                    column="delivered"
                    label="Réalisé"
                    sorted={sorted}
                    onBasculer={trierPar}
                    aDroite
                  />
                  {/* Qui s'en occupe ne se range pas : une colonne de jetons
                      n'a pas d'ordre que le lecteur aurait en tete. */}
                  <TableHead>Référents</TableHead>
                  <TableHead>Intervenants</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {screen.tree.map(({ mission, lots }) => {
                  const deplie = screen.estDeplie(mission.project.id);

                  return (
                    <Fragment key={mission.project.id}>
                      <MissionRow
                        mission={mission}
                        estLot={mission.project.kind === "work_package"}
                        lots={lots.length}
                        deplie={deplie}
                        onBasculer={() => screen.toggle(mission.project.id)}
                        maintenant={maintenant}
                        onOpen={() => panel.open(mission.project.id)}
                        onOpenFil={() => panel.open(mission.project.id, "updates")}
                      />
                      {deplie &&
                        lots.map((lot) => (
                          <MissionRow
                            key={lot.project.id}
                            mission={lot}
                            estLot
                            maintenant={maintenant}
                            onOpen={() => panel.open(lot.project.id)}
                            onOpenFil={() => panel.open(lot.project.id, "updates")}
                          />
                        ))}
                    </Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {screen.activities.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-2 text-sm font-medium text-slate-600">
              Activités hors projet
            </h2>
            <p className="mb-3 text-sm text-slate-500">
              Elles n&apos;ont ni phase ni estimé, et ne remontent jamais dans Monday.
              Sans elles, les jours ouvrés se reporteraient sur les projets.
            </p>
            <ul className="flex flex-wrap gap-2">
              {screen.activities.map((activity) => (
                <li
                  key={activity.project.id}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
                >
                  {activity.project.label}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <DeclareProjectDialog
        open={declaring}
        onOpenChange={setDeclaration}
        onConfirm={async (label) => {
          await screen.declare(label, "project");
        }}
      />

      <ImportProjectsDialog
        open={importing}
        onOpenChange={setImportation}
        onImport={screen.importCsv}
      />

      {panel.openedMission && (
        <ProjectPanel
          // L'onglet fait partie de la cle : rouvrir la meme mission sur son
          // fil doit remonter le panneau, qui choisit son onglet a l'ouverture.
          key={`${panel.openedMission}:${panel.ongletOuvert ?? ""}`}
          projectId={panel.openedMission}
          onglet={panel.ongletOuvert}
          onClose={panel.close}
          onMissionChanged={screen.refresh}
        />
      )}
    </PageLayout>
  );
}
