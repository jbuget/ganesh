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

/** Une mission proposee : `value` / `label` est la forme que Base UI sait lire. */
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
 * Ajout d'une mission a la matrice, depuis la derniere ligne du tableau.
 *
 * Les missions deja presentes sont retirees de la liste : on ne peut pas creer
 * deux lignes pour la meme mission.
 *
 * Le referentiel compte des dizaines de projets et de lots : le champ de
 * recherche en tete du menu evite de parcourir la liste entiere pour trouver
 * celui qu'on cherche. « Declarer un nouveau projet » reste en pied de menu,
 * hors du filtre : c'est justement quand aucune mission ne correspond qu'on en
 * a besoin.
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
