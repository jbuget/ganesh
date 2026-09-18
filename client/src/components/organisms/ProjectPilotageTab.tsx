"use client";

import { useState } from "react";

import { CategoryPicker } from "@/components/atoms/CategoryPicker";
import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { InlineNumberField } from "@/components/atoms/InlineNumberField";
import { ContributorsPicker } from "@/components/atoms/ContributorsPicker";
import { PhasePicker } from "@/components/atoms/PhasePicker";
import { PriorityPicker } from "@/components/atoms/PriorityPicker";
import { ProjectContributions } from "@/components/molecules/ProjectContributions";
import { ProjectLinksEditor } from "@/components/molecules/ProjectLinksEditor";
import { ProjectSubProjects } from "@/components/molecules/ProjectSubProjects";
import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";

interface ProjectPilotageTabProps {
  detail: ProjectDetailResponse;
  onChange: () => void | Promise<void>;
  enregistrerFiche: (
    departments: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
  changerPhase: (status: ProjectStatus) => Promise<void>;
  changerCaracteristiques: (champs: {
    category?: ProjectCategory | null;
    priority?: ProjectPriority | null;
    estimated_days?: number | null;
  }) => Promise<void>;
  ajouterLien: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  retirerLien: (linkId: number) => Promise<void>;
}

/**
 * One row of the sheet: its heading on the left, its value on the right.
 *
 * Fields stack rather than arrange themselves in columns: a sheet is scanned
 * top to bottom, and a constant heading width gives that scan something to lean
 * on.
 */
function Ligne({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="w-36 shrink-0 pt-0.5 text-sm text-slate-500">{titre}</span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

/**
 * The heading of a section of the sheet.
 *
 * Three blocks follow one another in the same column: their title must stand
 * out from their content, otherwise one no longer sees where one stops and the
 * next begins. The rule gives the break, the weight gives the level.
 */
function TitreSection({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
      {children}
    </h3>
  );
}

/**
 * What one needs to steer a mission.
 *
 * Characteristics at the top, consumption at the bottom: one looks first at
 * where the mission stands and who looks after it, then at what it covers, then
 * at what it has cost.
 */
export function ProjectPilotageTab({
  detail,
  onChange,
  enregistrerFiche,
  changerPhase,
  changerCaracteristiques,
  ajouterLien,
  retirerLien,
}: ProjectPilotageTabProps) {
  // Until anything is typed, the field shows what the server says: no local
  // copy to resynchronise on every reload.
  const [draft, setBrouillon] = useState<string | null>(null);
  const { project } = detail;
  const contacts = draft ?? project.business_contacts ?? "";

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <TitreSection>Informations</TitreSection>

        <div className="divide-y divide-slate-100">
          <Ligne titre="Phase">
            <PhasePicker status={project.status} onChange={changerPhase} />
          </Ligne>

          <Ligne titre="Priorité">
            <PriorityPicker
              value={project.priority}
              onChange={(priority) => changerCaracteristiques({ priority })}
            />
          </Ligne>

          <Ligne titre="Catégorie">
            <CategoryPicker
              value={project.category}
              onChange={(category) => changerCaracteristiques({ category })}
            />
          </Ligne>

          <Ligne titre="Départements">
            <DepartmentPicker
              values={detail.departments}
              onChange={(values) => enregistrerFiche(values, contacts.trim() || null)}
            />
          </Ligne>

          <Ligne titre="Estimé (build)">
            <InlineNumberField
              value={project.estimated_days}
              suffixe="jrs."
              invite="Estimer"
              onChange={(estimated_days) => changerCaracteristiques({ estimated_days })}
            />
          </Ligne>

          <Ligne titre="Référents projet">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.leads}
              role="lead"
              invite="Référents"
              onChange={onChange}
            />
          </Ligne>

          <Ligne titre="Intervenants">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.contributors}
              invite="Intervenants"
              onChange={onChange}
            />
          </Ligne>

          <Ligne titre="Contacts métier">
            <input
              type="text"
              value={contacts}
              placeholder="Qui appeler côté métier…"
              aria-label="Contacts métier"
              onChange={(event) => setBrouillon(event.target.value)}
              // Saved on leaving the field: nothing is written on every keystroke.
              onBlur={() => {
                if (draft === null) return;
                setBrouillon(null);
                void enregistrerFiche(detail.departments, draft.trim() || null);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") event.currentTarget.blur();
              }}
              className="-mx-1 w-full rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-slate-400 focus:outline-none"
            />
          </Ligne>

          <Ligne titre="Liens">
            <ProjectLinksEditor
              links={detail.links}
              onAdd={ajouterLien}
              onRemove={retirerLien}
            />
          </Ligne>
        </div>
      </section>

      <section className="space-y-2">
        <TitreSection>Sous-projets</TitreSection>
        <ProjectSubProjects sousProjets={detail.sub_projects} />
      </section>

      <section className="space-y-2">
        <TitreSection>Consommation</TitreSection>
        <ProjectContributions
          contributions={detail.contributions}
          total={detail.consumed_days}
        />
      </section>
    </div>
  );
}
