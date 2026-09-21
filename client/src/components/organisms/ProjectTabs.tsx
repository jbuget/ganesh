"use client";

import { ArchiveMissionDialog } from "@/components/atoms/ArchiveMissionDialog";
import { ArchivedCallout } from "@/components/atoms/ArchivedCallout";
import { AttachMissionDialog } from "@/components/atoms/AttachMissionDialog";
import { DeleteMissionDialog } from "@/components/atoms/DeleteMissionDialog";
import { MissionMenu } from "@/components/atoms/MissionMenu";
import { ProjectAttachmentsTab } from "@/components/organisms/ProjectAttachmentsTab";
import { ProjectAuditTab } from "@/components/organisms/ProjectAuditTab";
import { ProjectSteeringTab } from "@/components/organisms/ProjectSteeringTab";
import { ProjectSheetTab } from "@/components/organisms/ProjectSheetTab";
import { ProjectUpdatesTab } from "@/components/organisms/ProjectUpdatesTab";
import { useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { SheetFields } from "@/lib/service-sheet";
import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectStatus,
  SubProjectPolicy,
} from "@/lib/api/generated/model";

interface ProjectTabsProps {
  detail: ProjectDetailResponse;
  /** Which tab to open on; steering by default. */
  initialTab?: string | null;
  onChange: () => void | Promise<void>;
  saveSheet: (
    departments: Department[],
    businessContacts: string | null,
  ) => Promise<void>;
  saveDescription: (body: string) => Promise<void>;
  changePhase: (status: ProjectStatus) => Promise<void>;
  updateFields: (
    fields: SheetFields & {
      category?: ProjectCategory | null;
      estimated_days?: number | null;
    },
  ) => Promise<void>;
  saveRegistry: (registry: {
    stack: string[];
    tags: string[];
    depends_on: number[];
  }) => Promise<void>;
  addLink: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  removeLink: (linkId: number) => Promise<void>;
  addSubProject: (label: string) => Promise<void>;
  /** Makes the mission a work package of the project chosen. */
  attachTo: (parentId: number) => Promise<void>;
  /** Takes the work package back out as a project of its own. */
  detach: () => Promise<void>;
  /**
   * Takes the mission out of the reference list.
   *
   * The policy answers for the slices of a project cut into packages: the
   * server refuses the exit without it.
   */
  archive: (subProjects?: SubProjectPolicy) => Promise<void>;
  unarchive: () => Promise<void>;
  /**
   * Deletes the mission for good, once confirmed.
   *
   * The sheet dies with it: it is up to the screen holding these tabs to go
   * somewhere else afterwards.
   */
  deleteMission: () => Promise<void>;
}

/**
 * The five facets of a mission.
 *
 * Shared by the side panel and the full-page sheet: two arrangements of the
 * same content, so they do not drift apart.
 */
export function ProjectTabs({
  detail,
  initialTab,
  onChange,
  saveSheet,
  saveDescription,
  changePhase,
  updateFields,
  saveRegistry,
  addLink,
  removeLink,
  addSubProject,
  attachTo,
  detach,
  archive,
  unarchive,
  deleteMission,
}: ProjectTabsProps) {
  // Freezes the reference time for the duration of the visit: « il y a 3
  // min » must not recompute on every render, and the thread is only
  // loaded after mounting anyway — nothing is rendered server-side.
  const [now] = useState(() => new Date());
  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const [isAttachOpen, setAttachOpen] = useState(false);
  const [isArchiveOpen, setArchiveOpen] = useState(false);

  const { kind, parent_id: parentId } = detail.project;
  // Off-project work is not a slice of anything: absences and training belong
  // to no project. Everything else may move — a work package included, which
  // is how an aim taken at the wrong project is corrected.
  const belongsToAProject = kind === "work_package";
  const canBeAttached = kind !== "off_project";

  // Packages that already left settle nothing: the question is only about the
  // ones the archiving would leave behind, still steered on their own.
  const liveSubProjects = detail.sub_projects.filter((one) => one.is_active).length;

  return (
    <Tabs
      defaultValue={initialTab ?? "pilotage"}
      className="flex min-h-0 flex-1 flex-col gap-4"
    >
      {/* Above the tabs, therefore read before them: the state of the mission
          governs everything one is about to do to it. */}
      {!detail.project.is_active && (
        <ArchivedCallout archivedAt={detail.project.archived_at} />
      )}

      {/* The menu sits at the end of the tabs, on the side where the eye
          stops: one first picks what to read, and what acts on the whole
          mission waits aside. */}
      <div className="flex shrink-0 items-center gap-2">
        <TabsList className="min-w-0 flex-1">
          <TabsTrigger value="pilotage">Pilotage</TabsTrigger>
          <TabsTrigger value="updates">Mises à jour</TabsTrigger>
          <TabsTrigger value="fichiers">Fichiers</TabsTrigger>
          <TabsTrigger value="catalogue">Catalogue</TabsTrigger>
          <TabsTrigger value="audit">Journal</TabsTrigger>
        </TabsList>

        <MissionMenu
          archived={!detail.project.is_active}
          onAttach={canBeAttached ? () => setAttachOpen(true) : undefined}
          onDetach={belongsToAProject ? detach : undefined}
          parentLabel={detail.parent?.label ?? null}
          onArchive={liveSubProjects > 0 ? () => setArchiveOpen(true) : () => archive()}
          onUnarchive={unarchive}
          onDelete={() => setDeleteOpen(true)}
        />
      </div>

      {/* The packages the sheet already lists are the ones the dialog argues
          from, and the ones the server will settle. */}
      {isArchiveOpen && (
        <ArchiveMissionDialog
          open
          onOpenChange={setArchiveOpen}
          label={detail.project.label}
          subProjects={liveSubProjects}
          onConfirm={async (policy) => {
            setArchiveOpen(false);
            await archive(policy);
          }}
        />
      )}

      {/* What the sheet already shows is what the dialog argues from: the
          packages attached and the catalogue card are exactly what the server
          refuses a move over. */}
      {isAttachOpen && (
        <AttachMissionDialog
          open
          onOpenChange={setAttachOpen}
          missionId={detail.project.id}
          label={detail.project.label}
          subProjects={detail.sub_projects.length}
          published={detail.project.is_published}
          currentParentId={parentId}
          onConfirm={attachTo}
        />
      )}

      {/* The count the sheet already shows is what the dialog argues from:
          days declared and work packages attached are exactly what the
          server refuses a deletion over. */}
      <DeleteMissionDialog
        open={isDeleteOpen}
        onOpenChange={setDeleteOpen}
        label={detail.project.label}
        deletable={detail.project.is_deletable}
        consumedDays={detail.consumed_days}
        subProjects={detail.sub_projects.length}
        onConfirm={deleteMission}
      />

      <TabsContent value="pilotage">
        <ProjectSteeringTab
          detail={detail}
          onChange={onChange}
          saveSheet={saveSheet}
          changePhase={changePhase}
          updateFields={updateFields}
          addSubProject={addSubProject}
        />
      </TabsContent>

      <TabsContent value="updates">
        <ProjectUpdatesTab
          projectId={detail.project.id}
          now={now}
          onChange={onChange}
          // Coming from the counter, one comes to write: the cursor is already
          // waiting in the editor. Coming from the panel, one comes to read
          // first.
          focusComposer={initialTab === "updates"}
        />
      </TabsContent>

      <TabsContent value="fichiers">
        <ProjectAttachmentsTab projectId={detail.project.id} onChange={onChange} />
      </TabsContent>

      <TabsContent value="catalogue" className="min-h-0 flex-1">
        <ProjectSheetTab
          detail={detail}
          updateFields={updateFields}
          saveDescription={saveDescription}
          saveRegistry={saveRegistry}
          addLink={addLink}
          removeLink={removeLink}
        />
      </TabsContent>

      <TabsContent value="audit">
        <ProjectAuditTab projectId={detail.project.id} />
      </TabsContent>
    </Tabs>
  );
}
