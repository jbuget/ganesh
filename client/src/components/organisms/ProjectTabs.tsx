"use client";

import { ArchivedCallout } from "@/components/atoms/ArchivedCallout";
import { MissionMenu } from "@/components/atoms/MissionMenu";
import { ProjectPilotageTab } from "@/components/organisms/ProjectPilotageTab";
import { ProjectSheetTab } from "@/components/organisms/ProjectSheetTab";
import { ProjectUpdatesTab } from "@/components/organisms/ProjectUpdatesTab";
import { useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";

interface ProjectTabsProps {
  detail: ProjectDetailResponse;
  /** Which tab to open on; steering by default. */
  ongletInitial?: string | null;
  onChange: () => void | Promise<void>;
  saveSheet: (
    departments: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
  saveDescription: (body: string) => Promise<void>;
  changePhase: (status: ProjectStatus) => Promise<void>;
  updateFields: (fields: {
    category?: ProjectCategory | null;
    estimated_days?: number | null;
  }) => Promise<void>;
  addLink: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  removeLink: (linkId: number) => Promise<void>;
  archive: () => Promise<void>;
  desarchiver: () => Promise<void>;
}

/** What is still to be built, announced rather than left blank. */
function Chantier({ quoi }: { quoi: string }) {
  return <p className="py-8 text-center text-sm text-slate-400">{quoi}</p>;
}

/**
 * The four facets of a mission.
 *
 * Shared by the side panel and the full-page sheet: two arrangements of the
 * same content, so they do not drift apart.
 */
export function ProjectTabs({
  detail,
  ongletInitial,
  onChange,
  saveSheet,
  saveDescription,
  changePhase,
  updateFields,
  addLink,
  removeLink,
  archive,
  desarchiver,
}: ProjectTabsProps) {
  // Freezes the reference time for the duration of the visit: « il y a 3
  // min » must not recompute on every render, and the thread is only
  // loaded after mounting anyway — nothing is rendered server-side.
  const [now] = useState(() => new Date());

  return (
    <Tabs
      defaultValue={ongletInitial ?? "pilotage"}
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
          <TabsTrigger value="updates">Mises à day</TabsTrigger>
          <TabsTrigger value="fiche">Fiche service</TabsTrigger>
          <TabsTrigger value="audit">Journal</TabsTrigger>
        </TabsList>

        <MissionMenu
          archivee={!detail.project.is_active}
          onArchiver={archive}
          onDesarchiver={desarchiver}
        />
      </div>

      <TabsContent value="pilotage">
        <ProjectPilotageTab
          detail={detail}
          onChange={onChange}
          saveSheet={saveSheet}
          changePhase={changePhase}
          updateFields={updateFields}
          addLink={addLink}
          removeLink={removeLink}
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
          focusRedaction={ongletInitial === "updates"}
        />
      </TabsContent>

      <TabsContent value="fiche" className="min-h-0 flex-1">
        <ProjectSheetTab
          description={detail.project.description}
          onSave={saveDescription}
        />
      </TabsContent>

      <TabsContent value="audit">
        <Chantier quoi="Le journal arrive." />
      </TabsContent>
    </Tabs>
  );
}
