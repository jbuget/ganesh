"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import type { ProjectContributionResponse } from "@/lib/api/generated/model";
import { formatJoursDecimal, formatMonth } from "@/lib/dates";

interface ProjectContributionsProps {
  contributions: ProjectContributionResponse[];
  total: number;
}

/**
 * Qui a consomme quoi sur une mission.
 *
 * Une liste plutot qu'un tableau : on est deux a six sur une mission, et ce
 * qu'on y lit est une part, pas une grille de chiffres. Le detail mensuel se
 * deplie sous la ligne plutot que d'ouvrir un ecran : les autres contributeurs
 * restent sous les yeux, et c'est a eux qu'on se compare.
 */
export function ProjectContributions({
  contributions,
  total,
}: ProjectContributionsProps) {
  // Plusieurs lignes restent ouvertes a la fois : on deplie deux intervenants
  // justement pour confronter leurs mois.
  const [deplies, setDeplies] = useState<ReadonlySet<number>>(new Set());

  function basculer(memberId: number) {
    setDeplies((ouverts) => {
      const suivants = new Set(ouverts);
      if (!suivants.delete(memberId)) suivants.add(memberId);
      return suivants;
    });
  }

  if (contributions.length === 0) {
    return <p className="text-sm text-slate-400">Aucun temps déclaré</p>;
  }

  return (
    <ul className="space-y-0.5">
      {contributions.map((contribution) => {
        const ouvert = deplies.has(contribution.member.id);
        const part = total > 0 ? (contribution.jours / total) * 100 : 0;

        return (
          <li key={contribution.member.id}>
            <button
              type="button"
              aria-expanded={ouvert}
              onClick={() => basculer(contribution.member.id)}
              className="flex w-full cursor-pointer items-center gap-2 rounded px-1 py-1.5 text-left transition-colors hover:bg-slate-50"
            >
              <ChevronRight
                aria-hidden
                className={`size-3.5 shrink-0 text-slate-400 transition-transform ${ouvert ? "rotate-90" : ""}`}
              />
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[10px] font-medium text-slate-700">
                {contribution.member.initiales}
              </span>
              <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
                {contribution.member.display_name}
              </span>
              <span
                aria-hidden
                className="hidden h-1.5 w-24 shrink-0 overflow-hidden rounded-full bg-slate-100 sm:block"
              >
                <span
                  className="block h-full rounded-full bg-sky-500"
                  style={{ width: `${part}%` }}
                />
              </span>
              <span className="w-16 shrink-0 text-right text-sm tabular-nums text-slate-600">
                {formatJoursDecimal(contribution.jours)} jrs.
              </span>
            </button>

            {ouvert && (
              <ul className="mt-0.5 mb-1 ml-[3.25rem] space-y-0.5">
                {contribution.par_mois.map((mois) => (
                  <li
                    key={mois.mois}
                    className="flex items-center gap-2 text-sm text-slate-500"
                  >
                    <span className="min-w-0 flex-1 truncate capitalize">
                      {formatMonth(
                        Number(mois.mois.slice(0, 4)),
                        Number(mois.mois.slice(5, 7)),
                      )}
                    </span>
                    <span className="w-16 shrink-0 text-right tabular-nums">
                      {formatJoursDecimal(mois.jours)} jrs.
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
