"use client";

import { useState } from "react";

import { ChooseActivityDialog } from "@/components/atoms/ChooseActivityDialog";
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
 * One searches for a mission — that is the name one knows — and is asked for
 * the trade once it is found. Offering the pairs flat made every line read
 * « Développement » or « Pilotage » and buried the name being looked for,
 * which is the one thing anybody types here.
 *
 * **The trade is asked outside the list, in the dialog the reminder already
 * asks it in.** A panel hanging off the popup went with it: choosing a mission
 * closes the list, and anything the list carried was swept away before the
 * click on a trade could land — which is how one ended up unable to add a
 * second trade on a mission at all. A mission carrying a single free trade is
 * added by clicking it, there being nothing to ask.
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
  //: The mission whose trade is being asked, kept here rather than in the
  //: popup: the question outlives the list it was opened from.
  const [asking, setAsking] = useState<OfferedMission | null>(null);

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
   * Adds the mission, or asks which trade when there is a choice.
   *
   * Off-project work is declared on directly and carries none, so it is added
   * as itself.
   */
  function choose(mission: OfferedMission) {
    setOpen(false);
    if (mission.activities.length === 0) {
      onSelect(mission.projectId, null);
      return;
    }
    if (mission.activities.length === 1) {
      onSelect(mission.projectId, mission.activities[0].id);
      return;
    }
    setAsking(mission);
  }

  return (
    <>
      <Combobox
        items={groups}
        // The search reads the mission's name, without case or accents: it is
        // what one types, and the trade is asked once it is found.
        itemToStringLabel={(item: MissionItem) => item.value.projectLabel}
        filter={(item: MissionItem, query: string) => missionAnswers(item.value, query)}
        value={null}
        open={isOpen}
        onOpenChange={setOpen}
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

        <ComboboxContent className="max-h-72 min-w-80" aria-label="Ajouter un projet">
          <ComboboxInput placeholder="Rechercher un projet…" />

          <ComboboxEmpty>Aucun projet ne correspond.</ComboboxEmpty>

          <ComboboxList>
            {(group: MissionGroup) => (
              <ComboboxGroup key={group.value} items={group.items}>
                <ComboboxGroupLabel>{group.value}</ComboboxGroupLabel>
                <ComboboxCollection>
                  {(mission: MissionItem) => (
                    <ComboboxItem key={mission.value.projectId} value={mission}>
                      {/* The item wraps its children in a span that is both
                          flex-1 and truncate, so a mark set beside the label
                          falls to the next line: the row lays itself out. */}
                      <span className="flex w-full items-center gap-1.5">
                        <span className="min-w-0 flex-1 truncate">{mission.label}</span>
                        {mission.value.activities.length > 1 && (
                          // The application's own mark for « ceci ouvre une
                          // question » — the same one the two buttons of this
                          // selector carry. A chevron would promise a submenu
                          // opening beside the row, and nothing opens there.
                          <span className="shrink-0 text-muted-foreground" aria-hidden>
                            …
                          </span>
                        )}
                      </span>
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
              + Déclarer un nouveau projet…
            </button>
          </div>
        </ComboboxContent>
      </Combobox>

      {asking && (
        <ChooseActivityDialog
          open
          onOpenChange={(isAsked) => !isAsked && setAsking(null)}
          mission={asking.projectLabel}
          activities={asking.activities}
          onChoose={(activityId) => {
            setAsking(null);
            onSelect(asking.projectId, activityId);
          }}
        />
      )}
    </>
  );
}
