"use client";

import { useState } from "react";

import Link from "next/link";

import { CategoryMark } from "@/components/atoms/CategoryMark";
import { CategoryPicker } from "@/components/atoms/CategoryPicker";
import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { FollowMark } from "@/components/atoms/FollowMark";
import { ContributorsPicker } from "@/components/atoms/ContributorsPicker";
import { PhasePicker } from "@/components/atoms/PhasePicker";
import { PriorityPicker } from "@/components/atoms/PriorityPicker";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { TargetDateField } from "@/components/atoms/TargetDateField";
import { ProjectActivities } from "@/components/molecules/ProjectActivities";
import { useProjectActivities } from "@/lib/use-project-activities";
import { ProjectContributions } from "@/components/molecules/ProjectContributions";
import { TagPicker } from "@/components/molecules/TagPicker";
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
    go_live_date?: string | null;
  }) => Promise<void>;
  addSubProject: (label: string) => Promise<void>;
  /** Raises the mark the team follows the mission by, or lowers it. */
  toggleFollow: () => Promise<void>;
  /** Puts a tag on the mission by the name typed. */
  addTag: (name: string) => Promise<void>;
  removeTag: (tagId: number) => Promise<void>;
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
  addSubProject,
  toggleFollow,
  addTag,
  removeTag,
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
            <PhasePicker status={project.status} onChange={changePhase} />
          </SheetRow>

          {/* Off-project work carries no mark: an absence is not something
              anybody keeps an eye on. */}
          {project.kind !== "off_project" && (
            <SheetRow title="Suivi">
              <FollowMark
                followed={project.is_followed}
                labelled
                onToggle={() => void toggleFollow()}
                className="-ml-1"
              />
            </SheetRow>
          )}

          {/* What the team put on the mission to find it again — a client, a
              partner, a programme, a theme. Off-project work carries none, as
              it carries no mark: an absence has nothing to be found by. */}
          {project.kind !== "off_project" && (
            <SheetRow title="Tags">
              <TagPicker tags={detail.tags} onAdd={addTag} onRemove={removeTag} />
            </SheetRow>
          )}

          {/* Read under the phase, and posted here as well as on the
              roadmap: the day one moves a mission into « Recette » is the day
              one knows when it goes live, and the two gestures belong to the
              same minute. */}
          <SheetRow title="Mise en service">
            <TargetDateField
              value={project.go_live_date ?? null}
              missionLabel={project.label}
              onChange={(go_live_date) => updateFields({ go_live_date })}
            />
          </SheetRow>

          <SheetRow title="Priorité">
            <PriorityPicker
              value={project.priority}
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
                onChange={(category) => updateFields({ category })}
              />
            )}
          </SheetRow>

          <SheetRow title="Départements">
            <DepartmentPicker
              values={detail.departments}
              onChange={(values) => saveSheet(values, contacts.trim() || null)}
            />
          </SheetRow>

          <SheetRow title="Référents projet">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.leads}
              role="lead"
              label="Référents"
              onChange={onChange}
            />
          </SheetRow>

          {/* Who to call when it breaks, whoever happens to be on it this
              week: a developer who left the mission a year ago is still the
              one who knows why it was built that way. */}
          <SheetRow title="Référents techniques">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.tech_leads}
              role="tech_lead"
              label="Référents techniques"
              onChange={onChange}
            />
          </SheetRow>

          {/* « actuels » is the whole of it: the list is reworked twice a
              week and says who has their hands in it now, never who ever
              did. The consumption below answers that one. */}
          <SheetRow title="Intervenants actuels">
            <ContributorsPicker
              projectId={project.id}
              contributors={detail.contributors}
              label="Intervenants actuels"
              onChange={onChange}
            />
          </SheetRow>

          <SheetRow title="Contacts métier">
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
          </SheetRow>
        </div>
      </section>

      {/* The hierarchy stops at two levels, and off-project work carries
          nothing: a mission that cannot be a parent is not offered the
          section, rather than offering a move the server would refuse. */}
      {project.kind === "project" && (
        <section className="space-y-2">
          <SheetSectionTitle>Sous-projets</SheetSectionTitle>
          <ProjectSubProjects subProjects={detail.sub_projects} onAdd={addSubProject} />
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
