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

const enItems = (projects: ProjectResponse[]): MissionItem[] =>
  projects.map((project) => ({ value: project.id, label: project.label }));

/**
 * Adding a mission to the grid, from the last row of the table.
 *
 * Missions already there are taken out of the list: no two rows for the same
 * mission.
 *
 * The reference list runs to dozens of projects and work packages: the search
 * field at the top of the menu saves scanning the whole list for the one being
 * looked for. « Declarer un nouveau projet » stays at the foot of the
 * menu, outside the filter: it is precisely when no mission matches that one
 * needs it.
 */
export function MissionSelector({
  projects,
  excludedIds,
  onSelect,
  onDeclareNew,
  disabled = false,
}: MissionSelectorProps) {
  const { projets, horsProjet } = availableMissions(projects, excludedIds);
  const [ouvert, setOuvert] = useState(false);

  const groupes: MissionGroup[] = [];
  if (projets.length > 0) {
    groupes.push({ value: "Projets et lots", items: enItems(projets) });
  }
  if (horsProjet.length > 0) {
    groupes.push({ value: "Hors projet", items: enItems(horsProjet) });
  }

  return (
    <Combobox
      items={groupes}
      value={null}
      open={ouvert}
      onOpenChange={setOuvert}
      disabled={disabled}
      onValueChange={(mission) => {
        if (mission) onSelect((mission as MissionItem).value);
      }}
    >
      <ComboboxTrigger
        className="w-full text-muted-foreground"
        aria-label="Ajouter une mission"
      >
        <span className="truncate">+ Ajouter une mission…</span>
      </ComboboxTrigger>

      <ComboboxContent className="min-w-80" aria-label="Ajouter une mission">
        <ComboboxInput placeholder="Rechercher une mission…" />

        <ComboboxEmpty>Aucune mission ne correspond.</ComboboxEmpty>

        <ComboboxList>
          {(groupe: MissionGroup) => (
            <ComboboxGroup key={groupe.value} items={groupe.items}>
              <ComboboxGroupLabel>{groupe.value}</ComboboxGroupLabel>
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
              setOuvert(false);
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
