"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { IntervenantsPicker } from "@/components/atoms/IntervenantsPicker";
import { PhaseTimeline } from "@/components/atoms/PhaseTimeline";
import { ProjectLinksEditor } from "@/components/atoms/ProjectLinksEditor";
import { Textarea } from "@/components/ui/textarea";
import { categorie, libellePhase, pastillePhase } from "@/lib/board";
import { formatJoursDecimal } from "@/lib/dates";
import { useProjectDetail } from "@/lib/use-project-detail";

interface ProjectDetailPageProps {
  projectId: number;
}

/** Un bloc de la fiche : son intitule, et ce qu'il porte. */
function Champ({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h2 className="text-xs font-medium tracking-wide text-slate-500 uppercase">
        {titre}
      </h2>
      {children}
    </section>
  );
}

/** La fiche d'une mission : ce qu'elle est, qui s'en occupe, ou elle en est. */
export function ProjectDetailPage({ projectId }: ProjectDetailPageProps) {
  const fiche = useProjectDetail(projectId);
  // Tant qu'on n'a rien tape, le champ affiche ce que dit le serveur : pas de
  // copie locale a resynchroniser a chaque rechargement.
  const [brouillon, setBrouillon] = useState<string | null>(null);

  const detail = fiche.detail;
  const contacts = brouillon ?? detail?.project.contacts_metier ?? "";

  if (fiche.introuvable) {
    return (
      <main className="mx-auto max-w-[900px] p-6">
        <p className="text-sm text-slate-500">Cette mission n&apos;existe pas.</p>
      </main>
    );
  }

  if (!detail) {
    return (
      <main className="mx-auto max-w-[900px] p-6">
        <p className="text-sm text-slate-500">Chargement…</p>
      </main>
    );
  }

  const { project } = detail;
  const axe = categorie(project.categorie);

  return (
    <main className="mx-auto max-w-[900px] p-6">
      <Link
        href="/kanban"
        className="mb-4 inline-flex cursor-pointer items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-800"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Kanban
      </Link>

      <header className="mb-6">
        <h1 className="text-xl font-semibold">{project.label}</h1>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
          {project.statut && (
            <span className="flex items-center gap-1.5">
              <span
                aria-hidden
                className={`size-2.5 rounded-full ${pastillePhase(project.statut)}`}
              />
              {libellePhase(project.statut)}
            </span>
          )}
          {axe && (
            <span className={`rounded px-1.5 py-0.5 text-xs ${axe.classe}`}>
              {axe.libelle}
            </span>
          )}
          <span>
            {formatJoursDecimal(detail.consomme_j)}
            {project.estime_j ? `/${project.estime_j}` : ""} jrs.
            {project.estime_j ? " estimés" : " consommés"}
          </span>
        </p>
      </header>

      <div className="grid gap-6 sm:grid-cols-2">
        <Champ titre="Départements">
          <DepartmentPicker
            valeurs={detail.departements}
            onChange={(valeurs) =>
              fiche.enregistrerFiche(valeurs, contacts.trim() || null)
            }
          />
        </Champ>

        <Champ titre="Référents projet">
          <IntervenantsPicker
            projectId={projectId}
            intervenants={detail.referents}
            role="referent"
            invite="Référents"
            onChange={fiche.recharger}
          />
        </Champ>

        <Champ titre="Intervenants">
          <IntervenantsPicker
            projectId={projectId}
            intervenants={detail.intervenants}
            invite="Intervenants"
            onChange={fiche.recharger}
          />
        </Champ>

        <Champ titre="Contacts métier">
          <Textarea
            value={contacts}
            rows={3}
            placeholder="Qui appeler côté métier…"
            onChange={(event) => setBrouillon(event.target.value)}
            // Enregistre a la sortie du champ : on n'ecrit pas a chaque frappe.
            onBlur={() =>
              void fiche.enregistrerFiche(detail.departements, contacts.trim() || null)
            }
            className="text-sm"
          />
        </Champ>

        <Champ titre="Liens">
          <ProjectLinksEditor
            liens={detail.liens}
            onAdd={fiche.ajouterLien}
            onRemove={fiche.retirerLien}
          />
        </Champ>

        <Champ titre="Étapes franchies">
          <PhaseTimeline phases={detail.phases} />
        </Champ>

        {detail.contributions.length > 0 && (
          <Champ titre="Temps déclaré">
            <ul className="space-y-1">
              {detail.contributions.map((contribution) => (
                <li
                  key={contribution.member.id}
                  className="flex items-center gap-2 text-sm"
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
                    {contribution.member.initiales}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-slate-700">
                    {contribution.member.display_name}
                  </span>
                  <span className="tabular-nums text-slate-500">
                    {formatJoursDecimal(contribution.jours)} jrs.
                  </span>
                </li>
              ))}
            </ul>
          </Champ>
        )}
      </div>
    </main>
  );
}
