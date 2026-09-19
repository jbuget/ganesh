"use client";

import { useState } from "react";

import type { ProjectResponse } from "@/lib/api/generated/model";
import { availableMissions } from "@/lib/missions";
import {
  Combobox,
  ComboboxCollection,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxGroupLabel,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  ComboboxTrigger,
} from "@/components/ui/combobox";

interface MissionSelectorProps {
  projects: ProjectResponse[];
  excludedIds: number[];
  /** Missions the user contributes to, offered first. */
  assignedIds: number[];
  onSelect: (projectId: number) => void;
  onDeclareNew: () => void;
  disabled?: boolean;
}

/** An offered mission: `value` / `label` is the shape Base UI can read. */
interface MissionItem {
  value: number;
  label: string;
}

interface MissionGroup {
  value: string;
  items: MissionItem[];
}

const asItems = (projects: ProjectResponse[]): MissionItem[] =>
  projects.map((project) => ({ value: project.id, label: project.label }));

/**
 * Adding a mission to the grid, from the last row of the table.
 *
 * Missions already there are taken out of the list: no two rows for the same
 * mission.
 *
 * The reference list runs to dozens of projects and work packages: the search
 * field at the top of the menu saves scanning the whole list for the one being
 * looked for, and « Mes missions » puts the handful one actually works on
 * within reach without searching at all. « Declarer un nouveau projet » stays at the foot of the
 * menu, outside the filter: it is precisely when no mission matches that one
 * needs it.
 */
export function MissionSelector({
  projects,
  excludedIds,
  assignedIds,
  onSelect,
  onDeclareNew,
  disabled = false,
}: MissionSelectorProps) {
  const { mine, projectMissions, offProject } = availableMissions(
    projects,
    excludedIds,
    assignedIds,
  );
  const [isOpen, setOpen] = useState(false);

  const groups: MissionGroup[] = [];
  // First, and named after what ties them to the reader: these are the
  // projects the team put them on.
  if (mine.length > 0) {
    groups.push({ value: "Mes projets", items: asItems(mine) });
  }
  if (projectMissions.length > 0) {
    groups.push({ value: "Projets et lots", items: asItems(projectMissions) });
  }
  if (offProject.length > 0) {
    groups.push({ value: "Hors projet", items: asItems(offProject) });
  }

  return (
    <Combobox
      items={groups}
      value={null}
      open={isOpen}
      onOpenChange={setOpen}
      disabled={disabled}
      onValueChange={(mission) => {
        if (mission) onSelect((mission as MissionItem).value);
      }}
    >
      <ComboboxTrigger
        className="w-full text-muted-foreground"
        aria-label="Ajouter un projet"
      >
        <span className="truncate">+ Ajouter un projet…</span>
      </ComboboxTrigger>

      <ComboboxContent className="min-w-80" aria-label="Ajouter un projet">
        <ComboboxInput placeholder="Rechercher un projet…" />

        <ComboboxEmpty>Aucun projet ne correspond.</ComboboxEmpty>

        <ComboboxList>
          {(group: MissionGroup) => (
            <ComboboxGroup key={group.value} items={group.items}>
              <ComboboxGroupLabel>{group.value}</ComboboxGroupLabel>
              <ComboboxCollection>
                {(mission: MissionItem) => (
                  <ComboboxItem key={mission.value} value={mission}>
                    {mission.label}
                  </ComboboxItem>
                )}
              </ComboboxCollection>
            </ComboboxGroup>
          )}
        </ComboboxList>

        <div className="shrink-0 border-t border-border p-1">
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              onDeclareNew();
            }}
            className="w-full cursor-pointer rounded-md px-1.5 py-1 text-left text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            Déclarer un nouveau projet…
          </button>
        </div>
      </ComboboxContent>
    </Combobox>
  );
}
