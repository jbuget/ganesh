"use client";

import { useState } from "react";

import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { IntervenantsPicker } from "@/components/atoms/IntervenantsPicker";
import { ProjectContributions } from "@/components/molecules/ProjectContributions";
import { Textarea } from "@/components/ui/textarea";
import type { Department, ProjectDetailResponse } from "@/lib/api/generated/model";
import { categorie, libellePhase, pastillePhase } from "@/lib/board";
import { formatJoursDecimal } from "@/lib/dates";

interface ProjectPilotageTabProps {
  detail: ProjectDetailResponse;
  onChange: () => void | Promise<void>;
  enregistrerFiche: (
    departements: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
}

/** Un bloc de la fiche : son intitule, et ce qu'il porte. */
function Champ({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h3 className="text-xs font-medium tracking-wide text-slate-500 uppercase">
        {titre}
      </h3>
      {children}
    </section>
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
}: ProjectPilotageTabProps) {
  // Tant qu'on n'a rien tape, le champ affiche ce que dit le serveur : pas de
  // copie locale a resynchroniser a chaque rechargement.
  const [brouillon, setBrouillon] = useState<string | null>(null);
  const { project } = detail;
  const axe = categorie(project.categorie);
  const contacts = brouillon ?? project.contacts_metier ?? "";

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Champ titre="Phase">
          {project.statut ? (
            <p className="flex items-center gap-1.5 text-sm text-slate-700">
              <span
                aria-hidden
                className={`size-2.5 rounded-full ${pastillePhase(project.statut)}`}
              />
              {libellePhase(project.statut)}
            </p>
          ) : (
            <p className="text-sm text-slate-400">Hors projet</p>
          )}
        </Champ>

        <Champ titre="Catégorie">
          {axe ? (
            <span
              className={`inline-block rounded px-1.5 py-0.5 text-xs ${axe.classe}`}
            >
              {axe.libelle}
            </span>
          ) : (
            <p className="text-sm text-slate-400">Aucune</p>
          )}
        </Champ>

        <Champ titre="Départements">
          <DepartmentPicker
            valeurs={detail.departements}
            onChange={(valeurs) => enregistrerFiche(valeurs, contacts.trim() || null)}
          />
        </Champ>

        <Champ titre="Estimé (build)">
          <p className="text-sm text-slate-700">
            {project.estime_j
              ? `${formatJoursDecimal(project.estime_j)} jrs.`
              : "Non estimé"}
          </p>
        </Champ>

        <Champ titre="Référents projet">
          <IntervenantsPicker
            projectId={project.id}
            intervenants={detail.referents}
            role="referent"
            invite="Référents"
            onChange={onChange}
          />
        </Champ>

        <Champ titre="Intervenants">
          <IntervenantsPicker
            projectId={project.id}
            intervenants={detail.intervenants}
            invite="Intervenants"
            onChange={onChange}
          />
        </Champ>
      </div>

      <Champ titre="Contacts métier">
        <Textarea
          value={contacts}
          rows={2}
          placeholder="Qui appeler côté métier…"
          onChange={(event) => setBrouillon(event.target.value)}
          // Enregistre a la sortie du champ : on n'ecrit pas a chaque frappe.
          onBlur={() => {
            if (brouillon === null) return;
            setBrouillon(null);
            void enregistrerFiche(detail.departements, brouillon.trim() || null);
          }}
          className="text-sm"
        />
      </Champ>

      <Champ titre="Consommation">
        <ProjectContributions
          contributions={detail.contributions}
          total={detail.consomme_j}
        />
      </Champ>
    </div>
  );
}
