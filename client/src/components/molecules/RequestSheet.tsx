"use client";

import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { InlineTextArea } from "@/components/atoms/InlineTextArea";
import { InlineTextField } from "@/components/atoms/InlineTextField";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { SponsorsPicker } from "@/components/atoms/SponsorsPicker";
import type {
  Department,
  FillInRequestRequest,
  RequestResponse,
} from "@/lib/api/generated/model";

interface RequestSheetProps {
  request: RequestResponse;
  /** False as soon as it has been handed over: the sheet stops moving. */
  editable: boolean;
  onChange: (change: Partial<FillInRequestRequest>) => void | Promise<void>;
}

/**
 * What a need says, in the order one thinks it.
 *
 * The situation first, then who lives with it, then what would be true once
 * it is solved — the three the API asks for before it will take the request.
 * What follows is offered and never demanded: what it costs to do nothing,
 * when it would be wanted, and whatever solution the author already has in
 * mind.
 *
 * That last one sits at the bottom, on its own, and is the only field with a
 * word of warning under it: a need arriving as a solution is one nobody can
 * weigh any more.
 */
export function RequestSheet({ request, editable, onChange }: RequestSheetProps) {
  return (
    <>
      <SheetSectionTitle>Le besoin</SheetSectionTitle>

      <SheetRow title="Intitulé">
        <InlineTextField
          value={request.title}
          label="Intitulé"
          editable={editable}
          onChange={(title) => onChange({ title: title ?? request.title })}
        />
      </SheetRow>

      <SheetRow title="Départements">
        <DepartmentPicker
          values={request.departments}
          onChange={(departments: Department[]) => onChange({ departments })}
        />
      </SheetRow>

      <SheetRow title="Sponsors">
        <SponsorsPicker
          values={request.sponsors.map((sponsor) => sponsor.id)}
          editable={editable}
          onChange={(sponsor_ids) => onChange({ sponsor_ids })}
        />
      </SheetRow>

      <SheetRow title="Le problème">
        <InlineTextArea
          value={request.problem}
          label="Le problème"
          placeholder="Ce qui se passe aujourd'hui, et pourquoi c'est un problème"
          editable={editable}
          onChange={(problem) => onChange({ problem })}
        />
      </SheetRow>

      <SheetRow title="Qui est concerné">
        <InlineTextArea
          value={request.impact}
          label="Qui est concerné"
          placeholder="Qui le vit, combien de personnes, à quelle fréquence"
          editable={editable}
          onChange={(impact) => onChange({ impact })}
        />
      </SheetRow>

      <SheetRow title="Résultat attendu">
        <InlineTextArea
          value={request.expected_outcome}
          label="Résultat attendu"
          placeholder="Ce qui serait vrai une fois le besoin traité"
          editable={editable}
          onChange={(expected_outcome) => onChange({ expected_outcome })}
        />
      </SheetRow>

      <SheetSectionTitle>Pour situer</SheetSectionTitle>

      <SheetRow title="Coût de l'inaction">
        <InlineTextArea
          value={request.cost_of_inaction}
          label="Coût de l'inaction"
          placeholder="Ce que coûte le fait de ne rien faire"
          editable={editable}
          onChange={(cost_of_inaction) => onChange({ cost_of_inaction })}
        />
      </SheetRow>

      <SheetRow title="Échéance souhaitée">
        <InlineTextField
          value={request.desired_by}
          label="Échéance souhaitée"
          placeholder="2026-12-31"
          editable={editable}
          validate={(value) =>
            value && !/^\d{4}-\d{2}-\d{2}$/.test(value)
              ? "Une date au format AAAA-MM-JJ."
              : null
          }
          onChange={(desired_by) => onChange({ desired_by })}
        />
      </SheetRow>

      <SheetRow title="Piste envisagée">
        <div className="space-y-1">
          <InlineTextArea
            value={request.envisaged_solution}
            label="Piste envisagée"
            placeholder="Facultatif"
            editable={editable}
            onChange={(envisaged_solution) => onChange({ envisaged_solution })}
          />
          <p className="text-xs text-slate-400">
            Facultatif, et lu en dernier : c&apos;est le besoin qui est arbitré, pas la
            solution.
          </p>
        </div>
      </SheetRow>
    </>
  );
}
