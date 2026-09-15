"use client";

import type { ProjectResponse } from "@/lib/api/generated/model";

interface MissionSelectorProps {
  projects: ProjectResponse[];
  excludedIds: number[];
  onSelect: (projectId: number) => void;
  onDeclareNew: () => void;
  disabled: boolean;
}

const NEW_PROJECT = "__new__";

/**
 * Selecteur place sur la premiere cellule d'une nouvelle ligne.
 *
 * Les missions deja presentes dans la matrice sont retirees de la liste : on ne
 * peut pas creer deux lignes pour la meme mission.
 */
export function MissionSelector({
  projects,
  excludedIds,
  onSelect,
  onDeclareNew,
  disabled,
}: MissionSelectorProps) {
  const available = projects.filter((p) => !excludedIds.includes(p.id));
  const activities = available.filter((p) => p.kind === "hors_projet");
  const missions = available.filter((p) => p.kind !== "hors_projet");

  return (
    <select
      value=""
      disabled={disabled}
      aria-label="Ajouter une mission"
      className="w-full cursor-pointer rounded border border-dashed border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-500 disabled:cursor-not-allowed"
      onChange={(event) => {
        const { value } = event.target;
        if (!value) return;
        if (value === NEW_PROJECT) onDeclareNew();
        else onSelect(Number(value));
      }}
    >
      <option value="">+ Ajouter une mission…</option>
      {missions.length > 0 && (
        <optgroup label="Projets et lots">
          {missions.map((project) => (
            <option key={project.id} value={project.id}>
              {project.label}
            </option>
          ))}
        </optgroup>
      )}
      {activities.length > 0 && (
        <optgroup label="Hors projet">
          {activities.map((project) => (
            <option key={project.id} value={project.id}>
              {project.label}
            </option>
          ))}
        </optgroup>
      )}
      <optgroup label="Autre">
        <option value={NEW_PROJECT}>Déclarer un nouveau projet…</option>
      </optgroup>
    </select>
  );
}
