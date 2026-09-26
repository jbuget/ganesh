"use client";

import { useState } from "react";

import Link from "next/link";

import { CategoryMark } from "@/components/atoms/CategoryMark";
import { CategoryPicker } from "@/components/atoms/CategoryPicker";
import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { ContributorsPicker } from "@/components/atoms/ContributorsPicker";
import { PhasePicker } from "@/components/atoms/PhasePicker";
import { PhaseTimeline } from "@/components/atoms/PhaseTimeline";
import { PriorityPicker } from "@/components/atoms/PriorityPicker";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { TargetDateField } from "@/components/atoms/TargetDateField";
import { ProjectActivities } from "@/components/molecules/ProjectActivities";
import { useProjectActivities } from "@/lib/use-project-activities";
import { ProjectContributions } from "@/components/molecules/ProjectContributions";
import { ProjectSubProjects } from "@/components/molecules/ProjectSubProjects";
import type {
  Department,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";

interface ProjectSteeringTabProps {
  detail: ProjectDetailResponse;
  /**
   * The reference day of the visit, frozen by the tabs above.
   *
   * Handed down rather than read here: « en retard » must not be able to
   * change under the reader's eyes, and two dates on one sheet must be read
   * against the same day.
   */
  now: Date;
  onChange: () => void | Promise<void>;
  saveSheet: (
    departments: Department[],
    businessContacts: string | null,
  ) => Promise<void>;
  changePhase: (status: ProjectStatus) => Promise<void>;
  /**
   * Whether the mission may be steered from here.
   *
   * The whole tab hangs off it rather than each field: steering is one thing
   * one may or may not do, and a sheet half open would be a sheet nobody can
   * read the rights of.
   */
  editable: boolean;
  updateFields: (fields: {
    category?: ProjectCategory | null;
    priority?: ProjectPriority | null;
    estimated_days?: number | null;
    go_live_date?: string | null;
  }) => Promise<void>;
  addSubProject: (label: string) => Promise<void>;
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
  now,
  onChange,
  saveSheet,
  changePhase,
  editable,
  updateFields,
  addSubProject,
}: ProjectSteeringTabProps) {
  // Until anything is typed, the field shows what the server says: no local
  // copy to resynchronise on every reload.
  const [draft, setDraft] = useState<string | null>(null);
  const { project } = detail;
  // The mission's estimate follows from these, so every write replays the
  // sheet: the ratio shown above must never lag behind the budgets below.
  const activities = useProjectActivities(project.id, onChange);
  const contacts = draft ?? project.business_contacts ?? "";

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <SheetSectionTitle>Informations</SheetSectionTitle>

        <div className="divide-y divide-slate-100">
          <SheetRow title="Phase">
            <PhasePicker
              status={project.status}
              editable={editable}
              onChange={changePhase}
            />
          </SheetRow>

          {/* Read right after the phase: where the mission stands, then the
              day it is announced for. The reference list and the roadmap show
              the same date, and `isGoLiveLate` is what keeps the three from
              disagreeing about whether that day has gone by. */}
          <SheetRow title="Mise en service">
            <span className="text-sm">
              <TargetDateField
                value={project.go_live_date}
                missionLabel={project.label}
                status={project.status}
                today={now}
                editable={editable}
                onChange={(go_live_date) => updateFields({ go_live_date })}
              />
            </span>
          </SheetRow>

          <SheetRow title="Priorité">
            <PriorityPicker
              value={project.priority}
              editable={editable}
              onChange={(priority) => updateFields({ priority })}
            />
          </SheetRow>

          <SheetRow title="Catégorie">
            {project.kind === "work_package" ? (
              <InheritedCategory
                value={project.category}
                parentId={project.parent_id}
              />
            ) : (
              <CategoryPicker
                value={project.category}
                editable={editable}
                onChange={(category) => updateFields({ category })}
              />
            )}
          </SheetRow>

          <SheetRow title="Départements">
            <DepartmentPicker
              values={detail.departments}
              editable={editable}
              onChange={(values) => saveSheet(values, contacts.trim() || null)}
            />
          </SheetRow>

          <SheetRow title="Référents projet">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.leads}
              role="lead"
              label="Référents"
              editable={editable}
              onChange={onChange}
            />
          </SheetRow>

          <SheetRow title="Intervenants">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.contributors}
              label="Intervenants"
              editable={editable}
              onChange={onChange}
            />
          </SheetRow>

          <SheetRow title="Contacts métier">
            <input
              type="text"
              value={contacts}
              placeholder="Qui appeler côté métier…"
              aria-label="Contacts métier"
              readOnly={!editable}
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
              className={`-mx-1 w-full rounded px-1 py-0.5 text-sm transition-colors focus:outline-none ${
                editable
                  ? "hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-slate-400"
                  : ""
              }`}
            />
          </SheetRow>
        </div>
      </section>

      {/* How the mission got where it stands, under where it stands. The
          register has recorded every crossing since the phases existed; a
          project it never followed says so rather than showing an empty
          list. */}
      <section className="space-y-2">
        <SheetSectionTitle>Étapes franchies</SheetSectionTitle>
        <PhaseTimeline phases={detail.phases} />
      </section>

      {/* The hierarchy stops at two levels, and off-project work carries
          nothing: a mission that cannot be a parent is not offered the
          section, rather than offering a move the server would refuse. */}
      {project.kind === "project" && (
        <section className="space-y-2">
          <SheetSectionTitle>Sous-projets</SheetSectionTitle>
          <ProjectSubProjects
            subProjects={detail.sub_projects}
            onAdd={editable ? addSubProject : undefined}
          />
        </section>
      )}

      {/* Off-project work is declared on directly — absences carry neither
          estimate nor trade — so it is not offered the section rather than
          offering a gesture the server would refuse. */}
      {project.kind !== "off_project" && (
        <section className="space-y-2">
          <SheetSectionTitle>Activités</SheetSectionTitle>
          <ProjectActivities
            activities={activities.activities}
            editable={editable}
            onAdd={activities.add}
            onChange={activities.change}
            onArchive={activities.archive}
            onRemove={activities.remove}
            onUnarchive={activities.unarchive}
          />
        </section>
      )}

      <section className="space-y-2">
        <SheetSectionTitle>Consommation</SheetSectionTitle>
        <ProjectContributions
          contributions={detail.contributions}
          total={detail.consumed_days}
        />
      </section>
    </div>
  );
}
