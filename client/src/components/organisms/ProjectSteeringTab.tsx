"use client";

import { useState } from "react";

import Link from "next/link";

import { CategoryMark } from "@/components/atoms/CategoryMark";
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

interface ProjectSteeringTabProps {
  detail: ProjectDetailResponse;
  onChange: () => void | Promise<void>;
  saveSheet: (
    departments: Department[],
    businessContacts: string | null,
  ) => Promise<void>;
  changePhase: (status: ProjectStatus) => Promise<void>;
  updateFields: (fields: {
    category?: ProjectCategory | null;
    priority?: ProjectPriority | null;
    estimated_days?: number | null;
  }) => Promise<void>;
  addLink: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  removeLink: (linkId: number) => Promise<void>;
  addSubProject: (label: string) => Promise<void>;
}

/**
 * One row of the sheet: its heading on the left, its value on the right.
 *
 * Fields stack rather than arrange themselves in columns: a sheet is scanned
 * top to bottom, and a constant heading width gives that scan something to lean
 * on.
 */
function Row({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="w-36 shrink-0 pt-0.5 text-sm text-slate-500">{title}</span>
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
function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
      {children}
    </h3>
  );
}

/**
 * The axis a work package reads under: the one its project carries.
 *
 * It qualifies the product, not a slice of it. Two packages of one project
 * claiming two axes would leave the project itself with none, and its totals
 * would no longer add up to anything. The field is therefore read here and
 * changed on the project, for the project and all its packages at once — which
 * is why the line leads there rather than opening a picker.
 */
function InheritedCategory({
  value,
  parentId,
}: {
  value: ProjectCategory | null | undefined;
  parentId: number | null;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      {value ? (
        <CategoryMark value={value} />
      ) : (
        <span className="text-slate-400">Aucune</span>
      )}
      {parentId !== null && (
        <Link
          href={`/projects/${parentId}`}
          className="cursor-pointer text-xs text-slate-400 underline-offset-2 transition-colors hover:text-slate-700 hover:underline"
        >
          {value ? "Définie sur le projet" : "À définir sur le projet"}
        </Link>
      )}
    </div>
  );
}

/**
 * What one needs to steer a mission.
 *
 * Characteristics at the top, consumption at the bottom: one looks first at
 * where the mission stands and who looks after it, then at what it covers, then
 * at what it has cost.
 */
export function ProjectSteeringTab({
  detail,
  onChange,
  saveSheet,
  changePhase,
  updateFields,
  addLink,
  removeLink,
  addSubProject,
}: ProjectSteeringTabProps) {
  // Until anything is typed, the field shows what the server says: no local
  // copy to resynchronise on every reload.
  const [draft, setDraft] = useState<string | null>(null);
  const { project } = detail;
  const contacts = draft ?? project.business_contacts ?? "";

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <SectionTitle>Informations</SectionTitle>

        <div className="divide-y divide-slate-100">
          <Row title="Phase">
            <PhasePicker status={project.status} onChange={changePhase} />
          </Row>

          <Row title="Priorité">
            <PriorityPicker
              value={project.priority}
              onChange={(priority) => updateFields({ priority })}
            />
          </Row>

          <Row title="Catégorie">
            {project.kind === "work_package" ? (
              <InheritedCategory
                value={project.category}
                parentId={project.parent_id}
              />
            ) : (
              <CategoryPicker
                value={project.category}
                onChange={(category) => updateFields({ category })}
              />
            )}
          </Row>

          <Row title="Départements">
            <DepartmentPicker
              values={detail.departments}
              onChange={(values) => saveSheet(values, contacts.trim() || null)}
            />
          </Row>

          <Row title="Estimé (build)">
            <InlineNumberField
              value={project.estimated_days}
              suffix="jrs."
              label="Estimer"
              onChange={(estimated_days) => updateFields({ estimated_days })}
            />
          </Row>

          <Row title="Référents projet">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.leads}
              role="lead"
              label="Référents"
              onChange={onChange}
            />
          </Row>

          <Row title="Intervenants">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.contributors}
              label="Intervenants"
              onChange={onChange}
            />
          </Row>

          <Row title="Contacts métier">
            <input
              type="text"
              value={contacts}
              placeholder="Qui appeler côté métier…"
              aria-label="Contacts métier"
              onChange={(event) => setDraft(event.target.value)}
              // Saved on leaving the field: nothing is written on every keystroke.
              onBlur={() => {
                if (draft === null) return;
                setDraft(null);
                void saveSheet(detail.departments, draft.trim() || null);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") event.currentTarget.blur();
              }}
              className="-mx-1 w-full rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-slate-400 focus:outline-none"
            />
          </Row>

          <Row title="Liens">
            <ProjectLinksEditor
              links={detail.links}
              onAdd={addLink}
              onRemove={removeLink}
            />
          </Row>
        </div>
      </section>

      {/* The hierarchy stops at two levels, and off-project work carries
          nothing: a mission that cannot be a parent is not offered the
          section, rather than offering a move the server would refuse. */}
      {project.kind === "project" && (
        <section className="space-y-2">
          <SectionTitle>Sous-projets</SectionTitle>
          <ProjectSubProjects subProjects={detail.sub_projects} onAdd={addSubProject} />
        </section>
      )}

      <section className="space-y-2">
        <SectionTitle>Consommation</SectionTitle>
        <ProjectContributions
          contributions={detail.contributions}
          total={detail.consumed_days}
        />
      </section>
    </div>
  );
}
