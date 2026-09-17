"use client";

import { useState } from "react";

import { CategoryPicker } from "@/components/atoms/CategoryPicker";
import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { InlineNumberField } from "@/components/atoms/InlineNumberField";
import { IntervenantsPicker } from "@/components/atoms/IntervenantsPicker";
import { PhasePicker } from "@/components/atoms/PhasePicker";
import { PriorityPicker } from "@/components/atoms/PriorityPicker";
import { ProjectContributions } from "@/components/molecules/ProjectContributions";
import { ProjectLinksEditor } from "@/components/molecules/ProjectLinksEditor";
import { ProjectSubProjects } from "@/components/molecules/ProjectSubProjects";
import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectPriority,
  ProjectStatus,
} from "@/lib/api/generated/model";

interface ProjectPilotageTabProps {
  detail: ProjectDetailResponse;
  onChange: () => void | Promise<void>;
  enregistrerFiche: (
    departments: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
  changerPhase: (status: ProjectStatus) => Promise<void>;
  changerCaracteristiques: (champs: {
    category?: ProjectCategory | null;
    priority?: ProjectPriority | null;
    estimated_days?: number | null;
  }) => Promise<void>;
  ajouterLien: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  retirerLien: (linkId: number) => Promise<void>;
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
 * L'intitule d'une section de la fiche.
 *
 * Trois blocs se suivent dans la meme colonne : leur titre doit trancher sur
 * leur contenu, sinon on ne voit plus ou l'un s'arrete et ou le suivant
 * commence. Le filet donne la coupure, la graisse donne le niveau.
 */
function TitreSection({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
      {children}
    </h3>
  );
}

/**
 * Ce qu'il faut savoir pour piloter une mission.
 *
 * Les caracteristiques en haut, la consommation en bas : on regarde d'abord ou
 * en est la mission et qui s'en occupe, puis ce qu'elle couvre, puis ce qu'elle
 * a coute.
 */
export function ProjectPilotageTab({
  detail,
  onChange,
  enregistrerFiche,
  changerPhase,
  changerCaracteristiques,
  ajouterLien,
  retirerLien,
}: ProjectPilotageTabProps) {
  // Tant qu'on n'a rien tape, le champ affiche ce que dit le serveur : pas de
  // copie locale a resynchroniser a chaque rechargement.
  const [draft, setBrouillon] = useState<string | null>(null);
  const { project } = detail;
  const contacts = draft ?? project.business_contacts ?? "";

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <TitreSection>Informations</TitreSection>

        <div className="divide-y divide-slate-100">
          <Ligne titre="Phase">
            <PhasePicker status={project.status} onChange={changerPhase} />
          </Ligne>

          <Ligne titre="Priorité">
            <PriorityPicker
              value={project.priority}
              onChange={(priority) => changerCaracteristiques({ priority })}
            />
          </Ligne>

          <Ligne titre="Catégorie">
            <CategoryPicker
              value={project.category}
              onChange={(category) => changerCaracteristiques({ category })}
            />
          </Ligne>

          <Ligne titre="Départements">
            <DepartmentPicker
              values={detail.departments}
              onChange={(values) => enregistrerFiche(values, contacts.trim() || null)}
            />
          </Ligne>

          <Ligne titre="Estimé (build)">
            <InlineNumberField
              value={project.estimated_days}
              suffixe="jrs."
              invite="Estimer"
              onChange={(estimated_days) => changerCaracteristiques({ estimated_days })}
            />
          </Ligne>

          <Ligne titre="Référents projet">
            <IntervenantsPicker
              projectId={project.id}
              contributors={detail.leads}
              role="lead"
              invite="Référents"
              onChange={onChange}
            />
          </Ligne>

          <Ligne titre="Intervenants">
            <IntervenantsPicker
              projectId={project.id}
              contributors={detail.contributors}
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
                if (draft === null) return;
                setBrouillon(null);
                void enregistrerFiche(detail.departments, draft.trim() || null);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") event.currentTarget.blur();
              }}
              className="-mx-1 w-full rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-slate-400 focus:outline-none"
            />
          </Ligne>

          <Ligne titre="Liens">
            <ProjectLinksEditor
              links={detail.links}
              onAdd={ajouterLien}
              onRemove={retirerLien}
            />
          </Ligne>
        </div>
      </section>

      <section className="space-y-2">
        <TitreSection>Sous-projets</TitreSection>
        <ProjectSubProjects sousProjets={detail.sub_projects} />
      </section>

      <section className="space-y-2">
        <TitreSection>Consommation</TitreSection>
        <ProjectContributions
          contributions={detail.contributions}
          total={detail.consumed_days}
        />
      </section>
    </div>
  );
}
