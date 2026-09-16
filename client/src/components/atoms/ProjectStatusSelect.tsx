"use client";

import type { ProjectStatus } from "@/lib/api/generated/model";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/** Phases d'un projet, dans leur ordre nominal. */
export const STATUTS: { valeur: ProjectStatus; libelle: string }[] = [
  { valeur: "exploration", libelle: "Exploration" },
  { valeur: "cadrage", libelle: "Cadrage" },
  { valeur: "realisation", libelle: "Réalisation" },
  { valeur: "validation", libelle: "Validation" },
  { valeur: "exploitation", libelle: "Exploitation" },
];

const LIBELLES = new Map(STATUTS.map((s) => [s.valeur, s.libelle]));

interface ProjectStatusSelectProps {
  statut: ProjectStatus;
  onChange: (statut: ProjectStatus) => void;
}

/**
 * Change la phase d'une mission.
 *
 * Toute transition est permise, y compris un retour en arriere : un projet
 * peut repasser en cadrage apres une validation.
 */
export function ProjectStatusSelect({ statut, onChange }: ProjectStatusSelectProps) {
  return (
    <Select value={statut} onValueChange={(value) => onChange(value as ProjectStatus)}>
      <SelectTrigger size="sm" className="w-36" aria-label="Phase du projet">
        <SelectValue>
          {(value: string) => LIBELLES.get(value as ProjectStatus)}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {STATUTS.map(({ valeur, libelle }) => (
          <SelectItem key={valeur} value={valeur}>
            {libelle}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
