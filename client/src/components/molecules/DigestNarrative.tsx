import { Sparkles } from "lucide-react";

import { EmphasisedParagraphs } from "@/components/atoms/EmphasisedParagraphs";
import type { SpotlightResponse } from "@/lib/api/generated/model";
import { phaseLabel } from "@/lib/board";
import { missionName, spotlightFigures } from "@/lib/gazette";

interface DigestNarrativeProps {
  /** The editorial, when one held. */
  prose: string | null;
  spotlights: SpotlightResponse[];
  /** Which model wrote them: a reader weighs the text once they know. */
  model: string;
  /** The projects and people to be set in bold, wherever they appear. */
  names: string[];
}

/**
 * The month told, in one frame: the editorial, then the projects under the
 * spotlight.
 *
 * The two come from one answer of the model and are read as one text, so they
 * share a frame and a signature rather than reading as two generations. The
 * figures under each project's title are the register's, drawn beside the
 * text so that no number has to be taken from the prose.
 */
export function DigestNarrative({
  prose,
  spotlights,
  model,
  names,
}: DigestNarrativeProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-slate-50 px-5 py-4">
      {prose && <EmphasisedParagraphs text={prose} names={names} />}

      {spotlights.length > 0 && (
        <div className={prose ? "mt-4 border-t border-slate-200 pt-4" : ""}>
          <h3 className="text-sm font-semibold text-slate-900">Sous le projecteur</h3>
          <div className="mt-3 flex flex-col divide-y divide-slate-200">
            {spotlights.map((spotlight) => (
              <article key={spotlight.project_id} className="py-4 first:pt-0 last:pb-0">
                <h4 className="text-sm font-semibold text-slate-900">
                  {missionName(spotlight.label)}
                </h4>
                <p className="mt-0.5 mb-2 text-xs text-slate-500">
                  {[
                    spotlight.went_live
                      ? "Mis en service ce mois-ci"
                      : spotlight.status
                        ? phaseLabel(spotlight.status)
                        : null,
                    ...spotlightFigures(spotlight),
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                <EmphasisedParagraphs text={spotlight.text} names={names} />
              </article>
            ))}
          </div>
        </div>
      )}

      <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
        <Sparkles className="size-3.5 shrink-0" aria-hidden />
        Texte rédigé par {model} à partir des faits ci-dessous et des mises à jour de
        l&apos;équipe. Les chiffres, eux, viennent du journal.
      </p>
    </section>
  );
}
