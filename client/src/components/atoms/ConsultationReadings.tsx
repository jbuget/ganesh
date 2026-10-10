import type { ConsultationResponse } from "@/lib/api/generated/model";

interface ConsultationReadingsProps {
  consultations: ConsultationResponse[];
}

/**
 * What every tool the model asked for was passed, and read back word for word.
 *
 * Folded: a reading runs to pages, and one opens the one that explains the
 * answer — or the absence of one — rather than scrolling past all of them.
 */
export function ConsultationReadings({ consultations }: ConsultationReadingsProps) {
  return (
    <div className="space-y-1">
      <h3 className="text-xs font-medium text-slate-600">
        {consultations.length === 0
          ? "Aucun outil consulté"
          : "Ce que les outils ont lu"}
      </h3>
      {consultations.map((consultation, index) => (
        <details key={index} className="rounded border border-slate-200 text-xs">
          <summary className="cursor-pointer px-2 py-1 text-slate-700">
            <code>{consultation.tool}</code>{" "}
            <span className="text-slate-500">
              {JSON.stringify(consultation.arguments)}
            </span>
          </summary>
          <pre className="max-h-80 overflow-auto border-t border-slate-200 bg-slate-50 px-2 py-1.5 whitespace-pre-wrap text-slate-700">
            {consultation.result}
          </pre>
        </details>
      ))}
    </div>
  );
}
