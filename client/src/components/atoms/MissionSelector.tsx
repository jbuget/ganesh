"use client";

import type { ProjectResponse } from "@/lib/api/generated/model";
import { availableMissions } from "@/lib/missions";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface MissionSelectorProps {
  projects: ProjectResponse[];
  excludedIds: number[];
  onSelect: (projectId: number) => void;
  onDeclareNew: () => void;
  disabled?: boolean;
}

const NEW_PROJECT = "__new__";

/**
 * Ajout d'une mission a la matrice, depuis la barre d'outils.
 *
 * Les missions deja presentes sont retirees de la liste : on ne peut pas creer
 * deux lignes pour la meme mission.
 */
export function MissionSelector({
  projects,
  excludedIds,
  onSelect,
  onDeclareNew,
  disabled = false,
}: MissionSelectorProps) {
  const { projets, horsProjet } = availableMissions(projects, excludedIds);

  return (
    <Select
      value=""
      disabled={disabled}
      onValueChange={(value) => {
        if (value === NEW_PROJECT) onDeclareNew();
        else onSelect(Number(value));
      }}
    >
      <SelectTrigger className="w-56" aria-label="Ajouter une mission">
        <SelectValue placeholder="+ Ajouter une mission…" />
      </SelectTrigger>

      <SelectContent>
        {projets.length > 0 && (
          <SelectGroup>
            <SelectLabel>Projets et lots</SelectLabel>
            {projets.map((project) => (
              <SelectItem key={project.id} value={String(project.id)}>
                {project.label}
              </SelectItem>
            ))}
          </SelectGroup>
        )}

        {horsProjet.length > 0 && (
          <SelectGroup>
            <SelectLabel>Hors projet</SelectLabel>
            {horsProjet.map((project) => (
              <SelectItem key={project.id} value={String(project.id)}>
                {project.label}
              </SelectItem>
            ))}
          </SelectGroup>
        )}

        <SelectGroup>
          <SelectLabel>Autre</SelectLabel>
          <SelectItem value={NEW_PROJECT}>Déclarer un nouveau projet…</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
