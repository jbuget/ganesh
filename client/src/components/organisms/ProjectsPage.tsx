"use client";

import { Plus, Upload } from "lucide-react";
import { Fragment, useState } from "react";

import { DeclareProjectDialog } from "@/components/atoms/DeclareProjectDialog";
import { ImportProjectsDialog } from "@/components/atoms/ImportProjectsDialog";
import { MondayLink } from "@/components/atoms/MondayLink";
import { ProjectStatusSelect } from "@/components/atoms/ProjectStatusSelect";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ProjectResponse, ProjectStatus } from "@/lib/api/generated/model";
import { useProjectsScreen } from "@/lib/use-projects";

/** Une mission dans le tableau, un lot etant decale sous son projet. */
function MissionRow({
  project,
  estLot,
  onChangeStatus,
  onChangeEstimate,
  onArchive,
}: {
  project: ProjectResponse;
  estLot: boolean;
  onChangeStatus: (statut: ProjectStatus) => void;
  onChangeEstimate: (estime: number | null) => void;
  onArchive: () => void;
}) {
  return (
    <TableRow>
      <TableCell className={estLot ? "pl-10 text-slate-600" : "font-medium"}>
        {estLot && <span className="mr-2 text-slate-400">└</span>}
        {project.label}
      </TableCell>

      <TableCell>
        {project.statut && (
          <ProjectStatusSelect statut={project.statut} onChange={onChangeStatus} />
        )}
      </TableCell>

      <TableCell className="text-right">
        <input
          type="number"
          min={0}
          step={0.5}
          defaultValue={project.estime_j ?? ""}
          aria-label={`Estimé de ${project.label}`}
          className="w-20 rounded border border-slate-300 px-2 py-1 text-right text-sm"
          onBlur={(event) => {
            const valeur = event.target.value.trim();
            const estime = valeur === "" ? null : Number(valeur);
            if (estime !== (project.estime_j ?? null)) onChangeEstimate(estime);
          }}
        />
      </TableCell>

      <TableCell>
        <MondayLink project={project} />
      </TableCell>

      <TableCell className="text-right">
        <Button variant="ghost" size="sm" onClick={onArchive}>
          Archiver
        </Button>
      </TableCell>
    </TableRow>
  );
}

/** Referentiel des missions : projets, lots et activites hors projet. */
export function ProjectsPage() {
  const ecran = useProjectsScreen();
  const [declaration, setDeclaration] = useState(false);
  const [importation, setImportation] = useState(false);

  return (
    <main className="mx-auto max-w-[1600px] p-6">
      <header className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold">Référentiel des missions</h1>
          <p className="text-sm text-slate-500">
            Ouvert à toute l&apos;équipe. Chaque modification est tracée.
          </p>
        </div>

        <div className="flex items-center gap-3">
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
        </div>
      </header>

      {ecran.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Mission</TableHead>
            <TableHead className="w-40">Phase</TableHead>
            <TableHead className="w-28 text-right">Estimé (j)</TableHead>
            <TableHead className="w-36">Monday</TableHead>
            <TableHead className="w-28" />
          </TableRow>
        </TableHeader>

        <TableBody>
          {ecran.arbre.length === 0 && !ecran.isLoading && (
            <TableRow>
              <TableCell colSpan={5} className="py-8 text-center text-slate-500">
                Aucun projet. Déclarez-en un ou importez votre référentiel.
              </TableCell>
            </TableRow>
          )}

          {ecran.arbre.map(({ project, lots }) => (
            <Fragment key={project.id}>
              <MissionRow
                project={project}
                estLot={project.kind === "lot"}
                onChangeStatus={(statut) => ecran.changeStatus(project.id, statut)}
                onChangeEstimate={(estime) => ecran.setEstimate(project.id, estime)}
                onArchive={() => ecran.archive(project.id, false)}
              />
              {lots.map((lot) => (
                <MissionRow
                  key={lot.id}
                  project={lot}
                  estLot
                  onChangeStatus={(statut) => ecran.changeStatus(lot.id, statut)}
                  onChangeEstimate={(estime) => ecran.setEstimate(lot.id, estime)}
                  onArchive={() => ecran.archive(lot.id, false)}
                />
              ))}
            </Fragment>
          ))}
        </TableBody>
      </Table>

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
    </main>
  );
}
