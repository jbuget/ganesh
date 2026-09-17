"use client";

import { useState } from "react";

import { CategoryPicker } from "@/components/atoms/CategoryPicker";
import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { InlineNumberField } from "@/components/atoms/InlineNumberField";
import { IntervenantsPicker } from "@/components/atoms/IntervenantsPicker";
import { PhasePicker } from "@/components/atoms/PhasePicker";
import { ProjectContributions } from "@/components/molecules/ProjectContributions";
import type {
  Department,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";

interface ProjectPilotageTabProps {
  detail: ProjectDetailResponse;
  onChange: () => void | Promise<void>;
  enregistrerFiche: (
    departements: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
  changerPhase: (statut: ProjectStatus) => Promise<void>;
  changerCaracteristiques: (champs: {
    categorie?: ProjectCategory | null;
    estime_j?: number | null;
  }) => Promise<void>;
}

/**
 * Une ligne de la fiche : son intitule a gauche, sa valeur a droite.
 *
 * Les champs s'empilent plutot que de se ranger en colonnes : on parcourt une
 * fiche du regard de haut en bas, et une largeur d'intitule constante donne un
 * point d'appui a ce parcours.
 */
function Ligne({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="w-36 shrink-0 pt-0.5 text-sm text-slate-500">{titre}</span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

/**
 * Ce qu'il faut savoir pour piloter une mission.
 *
 * Les caracteristiques en haut, la consommation en bas : on regarde d'abord ou
 * en est la mission et qui s'en occupe, puis ce qu'elle a coute.
 */
export function ProjectPilotageTab({
  detail,
  onChange,
  enregistrerFiche,
  changerPhase,
  changerCaracteristiques,
}: ProjectPilotageTabProps) {
  // Tant qu'on n'a rien tape, le champ affiche ce que dit le serveur : pas de
  // copie locale a resynchroniser a chaque rechargement.
  const [brouillon, setBrouillon] = useState<string | null>(null);
  const { project } = detail;
  const contacts = brouillon ?? project.contacts_metier ?? "";

  return (
    <div className="space-y-5">
      <div className="divide-y divide-slate-100">
        <Ligne titre="Phase">
          <PhasePicker statut={project.statut} onChange={changerPhase} />
        </Ligne>

        <Ligne titre="Catégorie">
          <CategoryPicker
            valeur={project.categorie}
            onChange={(categorie) => changerCaracteristiques({ categorie })}
          />
        </Ligne>

        <Ligne titre="Départements">
          <DepartmentPicker
            valeurs={detail.departements}
            onChange={(valeurs) => enregistrerFiche(valeurs, contacts.trim() || null)}
          />
        </Ligne>

        <Ligne titre="Estimé (build)">
          <InlineNumberField
            valeur={project.estime_j}
            suffixe="jrs."
            invite="Estimer"
            onChange={(estime_j) => changerCaracteristiques({ estime_j })}
          />
        </Ligne>

        <Ligne titre="Référents projet">
          <IntervenantsPicker
            projectId={project.id}
            intervenants={detail.referents}
            role="referent"
            invite="Référents"
            onChange={onChange}
          />
        </Ligne>

        <Ligne titre="Intervenants">
          <IntervenantsPicker
            projectId={project.id}
            intervenants={detail.intervenants}
            invite="Intervenants"
            onChange={onChange}
          />
        </Ligne>

        <Ligne titre="Contacts métier">
          <input
            type="text"
            value={contacts}
            placeholder="Qui appeler côté métier…"
            aria-label="Contacts métier"
            onChange={(event) => setBrouillon(event.target.value)}
            // Enregistre a la sortie du champ : on n'ecrit pas a chaque frappe.
            onBlur={() => {
              if (brouillon === null) return;
              setBrouillon(null);
              void enregistrerFiche(detail.departements, brouillon.trim() || null);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") event.currentTarget.blur();
            }}
            className="-mx-1 w-full rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-slate-400 focus:outline-none"
          />
        </Ligne>
      </div>

      <section className="space-y-1.5">
        <h3 className="text-xs font-medium tracking-wide text-slate-500 uppercase">
          Consommation
        </h3>
        <ProjectContributions
          contributions={detail.contributions}
          total={detail.consomme_j}
        />
      </section>
    </div>
  );
}
