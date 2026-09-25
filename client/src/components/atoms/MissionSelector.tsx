"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { missionAnswers, offeredMissions, type OfferedMission } from "@/lib/missions";
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
  missions: ProjectListItemResponse[];
  /** Rows already on the grid, as « mission:activity » keys. */
  excludedKeys: string[];
  /** Missions the user contributes to, offered first. */
  assignedIds: number[];
  onSelect: (projectId: number, activityId: number | null) => void;
  onDeclareNew: () => void;
  disabled?: boolean;
}

/** An offered mission, in the shape Base UI reads. */
interface MissionItem {
  value: OfferedMission;
  label: string;
}

interface MissionGroup {
  value: string;
  items: MissionItem[];
}

const asItems = (missions: OfferedMission[]): MissionItem[] =>
  missions.map((mission) => ({ value: mission, label: mission.projectLabel }));

/**
 * Adding a row to the grid, in two moves: the mission, then the trade.
 *
 * One searches for a mission — that is the name one knows — and chooses the
 * trade once it is found. Offering the pairs flat made every line read
 * « Développement » or « Delivery » and buried the name being looked for,
 * which is the one thing anybody types here.
 *
 * The trades open beside the mission rather than under it: a mission carries
 * two or three, and folding them into the list would put back the flat list
 * this exists to replace. A mission carrying a single free trade is added by
 * clicking it — there is nothing to choose.
 *
 * What is already on the month is out of the list: no two rows for the same
 * mission and trade, and a mission whose every trade is taken drops out.
 */
export function MissionSelector({
  missions,
  excludedKeys,
  assignedIds,
  onSelect,
  onDeclareNew,
  disabled = false,
}: MissionSelectorProps) {
  const [isOpen, setOpen] = useState(false);
  const [opened, setOpened] = useState<OfferedMission | null>(null);

  const offered = offeredMissions(missions, excludedKeys);
  const mine = offered.filter(
    (mission) =>
      mission.kind !== "off_project" && assignedIds.includes(mission.projectId),
  );
  const projectMissions = offered.filter(
    (mission) =>
      mission.kind !== "off_project" && !assignedIds.includes(mission.projectId),
  );
  const offProject = offered.filter((mission) => mission.kind === "off_project");

  const groups: MissionGroup[] = [];
  if (mine.length > 0) {
    groups.push({ value: "Mes projets", items: asItems(mine) });
  }
  if (projectMissions.length > 0) {
    groups.push({ value: "Projets et lots", items: asItems(projectMissions) });
  }
  if (offProject.length > 0) {
    groups.push({ value: "Hors projet", items: asItems(offProject) });
  }

  /**
   * Adds the mission, or opens its trades when there is a choice.
   *
   * Off-project work is declared on directly and carries none, so it is added
   * as itself.
   */
  function choose(mission: OfferedMission) {
    if (mission.activities.length === 0) {
      setOpen(false);
      onSelect(mission.projectId, null);
      return;
    }
    if (mission.activities.length === 1) {
      setOpen(false);
      onSelect(mission.projectId, mission.activities[0].id);
      return;
    }
    setOpened(mission);
  }

  return (
    <Combobox
      items={groups}
      // The search reads the mission's name, without case or accents: it is
      // what one types, and the trades are chosen once it is found.
      itemToStringLabel={(item: MissionItem) => item.value.projectLabel}
      filter={(item: MissionItem, query: string) => missionAnswers(item.value, query)}
      value={null}
      open={isOpen}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setOpened(null);
      }}
      disabled={disabled}
      onValueChange={(mission) => {
        if (mission) choose((mission as MissionItem).value);
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

        <div className="flex min-h-0">
          <ComboboxList className="min-w-0 flex-1">
            {(group: MissionGroup) => (
              <ComboboxGroup key={group.value} items={group.items}>
                <ComboboxGroupLabel>{group.value}</ComboboxGroupLabel>
                <ComboboxCollection>
                  {(mission: MissionItem) => (
                    <ComboboxItem
                      key={mission.value.projectId}
                      value={mission}
                      onMouseEnter={() => setOpened(mission.value)}
                    >
                      <span className="truncate">{mission.label}</span>
                      {mission.value.activities.length > 1 && (
                        <ChevronRight
                          className="ml-auto size-3.5 shrink-0 text-muted-foreground"
                          aria-hidden
                        />
                      )}
                    </ComboboxItem>
                  )}
                </ComboboxCollection>
              </ComboboxGroup>
            )}
          </ComboboxList>

          {opened && opened.activities.length > 1 && (
            <div
              className="w-48 shrink-0 border-l border-border p-1"
              aria-label={`Activités de ${opened.projectLabel}`}
            >
              <p className="truncate px-1.5 py-1 text-xs text-muted-foreground">
                {opened.projectLabel}
              </p>
              {opened.activities.map((activity) => (
                <button
                  key={activity.id}
                  type="button"
                  onClick={() => {
                    setOpen(false);
                    onSelect(opened.projectId, activity.id);
                  }}
                  className="w-full cursor-pointer truncate rounded-md px-1.5 py-1 text-left text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                >
                  {activity.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="shrink-0 border-t border-border p-1">
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              onDeclareNew();
            }}
            className="w-full cursor-pointer rounded-md px-1.5 py-1 text-left text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            + Déclarer un nouveau projet…
          </button>
        </div>
      </ComboboxContent>
    </Combobox>
  );
}
