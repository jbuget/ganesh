import type { AssistantIndicatorsResponse } from "@/lib/api/generated/model";
import { causeLabel, count, seconds, share } from "@/lib/assistant-study";
import { formatSpelledDate } from "@/lib/dates";
import { plural } from "@/lib/plurals";
import { parisDay } from "@/lib/instants";

interface AssistantIndicatorsBandProps {
  indicators: AssistantIndicatorsResponse;
}

/**
 * What the exchanges kept say about the assistant, in figures.
 *
 * Read before the table: whether the answers help, why the ones that do not
 * went wrong, how long people wait, and which tools carry the load. Figures
 * rather than a chart — each answers its own question, and none is a trend.
 *
 * The wait reads its slow tail beside its median: a median of five seconds
 * hides the one answer in twenty that took thirty.
 */
export function AssistantIndicatorsBand({ indicators }: AssistantIndicatorsBandProps) {
  const asked = indicators.questions;
  const figures: { label: string; value: string; detail?: string }[] = [
    {
      label: "Réponses",
      value: count(asked),
      detail: `${count(indicators.conversations)} ${plural(indicators.conversations, "conversation")}, ${count(indicators.askers)} ${plural(indicators.askers, "personne")}`,
    },
    {
      label: "Sans réponse",
      value: count(indicators.unanswered),
      // Out of everything asked: a question left unanswered is not among the
      // questions counted on the left, it is beside them.
      detail: `${share(indicators.unanswered, asked + indicators.unanswered)} des questions posées`,
    },
    {
      label: "Jugées utiles",
      // Among the answers somebody judged: silence is not a « non », and an
      // assistant nobody has thumbed yet does not help « 0 % » of the time.
      value: share(indicators.helpful, indicators.helpful + indicators.unhelpful),
      detail: `${count(indicators.unhelpful)} pas ${plural(indicators.unhelpful, "utile")}, ${count(indicators.unjudged)} sans avis`,
    },
    {
      label: "Temps de réponse",
      value: seconds(indicators.median_elapsed_ms),
      detail: `médiane ; ${seconds(indicators.p95_elapsed_ms)} pour 95 %`,
    },
    {
      label: "Tokens",
      value: count(indicators.input_tokens + indicators.output_tokens),
      detail: `${count(indicators.input_tokens)} lus, ${count(indicators.output_tokens)} écrits`,
    },
  ];

  return (
    <section aria-label="Indicateurs" className="space-y-4">
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {figures.map((figure) => (
          <div key={figure.label} className="space-y-0.5">
            <dt className="text-xs text-slate-500">{figure.label}</dt>
            <dd className="text-xl font-semibold text-slate-900 tabular-nums">
              {figure.value}
            </dd>
            {figure.detail && (
              <dd className="text-xs text-slate-500">{figure.detail}</dd>
            )}
          </div>
        ))}
      </dl>

      <div className="grid max-w-2xl gap-x-12 gap-y-4 text-sm sm:grid-cols-2">
        <div>
          <h3 className="mb-1 text-xs text-slate-500">Annotations</h3>
          <ul className="space-y-0.5 text-slate-700">
            {indicators.causes.map((held) => (
              <li key={held.cause} className="flex justify-between gap-4">
                <span>{causeLabel(held.cause)}</span>
                <span className="tabular-nums">{count(held.count)}</span>
              </li>
            ))}
            <li className="flex justify-between gap-4 text-slate-500">
              <span>Pas encore annotées</span>
              <span className="tabular-nums">{count(indicators.unannotated)}</span>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="mb-1 text-xs text-slate-500">Outils les plus appelés</h3>
          {indicators.tools.length === 0 ? (
            <p className="text-slate-500">Aucun outil appelé.</p>
          ) : (
            <ul className="space-y-0.5 text-slate-700">
              {indicators.tools.slice(0, 6).map((held) => (
                <li key={held.tool} className="flex justify-between gap-4">
                  <code className="text-xs">{held.tool}</code>
                  <span className="tabular-nums">{count(held.count)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Nothing is purged yet: the screen says how far back one can look
          rather than letting a period end silently at the first exchange. */}
      <p className="text-xs text-slate-500">
        {indicators.kept_since
          ? `Tous les échanges sont conservés depuis le premier, le ${formatSpelledDate(parisDay(indicators.kept_since))}.`
          : "Aucun échange conservé pour l'instant."}
      </p>
    </section>
  );
}
