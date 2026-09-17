"use client";

import { Plus, Upload } from "lucide-react";
import { Fragment, useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { ImportProjectsDialog } from "@/components/atoms/ImportProjectsDialog";
import { MissionListItem } from "@/components/atoms/MissionListItem";
import { PageHeader } from "@/components/atoms/PageHeader";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { Button } from "@/components/ui/button";
import { useMissionOuverte } from "@/lib/mission-ouverte";
import { useProjectsScreen } from "@/lib/use-projects";

/**
 * Le referentiel des missions.
 *
 * La liste ne montre que des noms et n'ouvre qu'une chose : le panneau de la
 * mission, celui-la meme que le kanban. Tout ce qui se modifie s'y fait, d'un
 * seul endroit — une liste qui edite en place multiplierait les chemins vers la
 * meme donnee, et les ferait diverger.
 */
export function ProjectsPage() {
  const ecran = useProjectsScreen();
  const panneau = useMissionOuverte();
  const [declaration, setDeclaration] = useState(false);
  const [importation, setImportation] = useState(false);

  return (
    <main className="p-6">
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

      {/* La liste reste etroite : un nom qui court sur 2000 px ne se lit plus. */}
      <div className="max-w-[900px]">
        {ecran.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {ecran.arbre.length === 0 && !ecran.isLoading && (
          <p className="py-8 text-center text-sm text-slate-500">
            Aucun projet. Déclarez-en un ou importez votre référentiel.
          </p>
        )}

        <ul className="divide-y divide-slate-100">
          {ecran.arbre.map(({ project, lots }) => (
            <Fragment key={project.id}>
              <MissionListItem
                label={project.label}
                estLot={project.kind === "lot"}
                onOpen={() => panneau.ouvrir(project.id)}
              />
              {lots.map((lot) => (
                <MissionListItem
                  key={lot.id}
                  label={lot.label}
                  estLot
                  onOpen={() => panneau.ouvrir(lot.id)}
                />
              ))}
            </Fragment>
          ))}
        </ul>

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
                  key={activite.id}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
                >
                  {activite.label}
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
    </main>
  );
}
