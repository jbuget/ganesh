"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";

import { InlineDateField } from "@/components/atoms/InlineDateField";
import { InlineTextField } from "@/components/atoms/InlineTextField";
import type { MilestoneResponse } from "@/lib/api/generated/model";
import { isMilestoneLate } from "@/lib/milestones";

interface ProjectMilestonesProps {
  milestones: MilestoneResponse[];
  /**
   * The reference day of the visit, frozen by the tabs above.
   *
   * Handed down rather than read here: « en retard » must not be able to
   * change under the reader's eyes, and every date on one sheet must be read
   * against the same day.
   */
  now: Date;
  /**
   * Whether the reader may post a date on this mission.
   *
   * A guest reads the application whole and declares nothing into it: the
   * gestures are simply not offered, the API refusing them anyway.
   */
  editable: boolean;
  onAdd: (label: string, expectedOn: string) => void | Promise<void>;
  onChange: (
    milestoneId: number,
    fields: { label?: string; expected_on?: string; reached_on?: string | null },
  ) => void | Promise<void>;
  onRemove: (milestoneId: number) => void | Promise<void>;
}

/**
 * The dates a mission answers for: the day each is announced, and the day it
 * happened.
 *
 * Read in the order they happen, reached or not: a list of dates is a
 * timeline, and folding the crossed ones to the bottom would break the one
 * reading it exists for — what came before what.
 *
 * A milestone carries a free label and no type. What a mission is answerable
 * for is proper to it — « bascule RDS », « COPIL du 12 » — and a closed list
 * would either be too short to name any of it, or overlap the phases above,
 * which are dated on their own when a card crosses a column.
 */
export function ProjectMilestones({
  milestones,
  now,
  editable,
  onAdd,
  onChange,
  onRemove,
}: ProjectMilestonesProps) {
  const [label, setLabel] = useState("");
  const [expectedOn, setExpectedOn] = useState("");
  const [posting, setPosting] = useState(false);

  const complete = label.trim() !== "" && expectedOn !== "";

  async function post() {
    if (!complete || posting) return;
    setPosting(true);
    try {
      await onAdd(label.trim(), expectedOn);
      setLabel("");
      setExpectedOn("");
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="space-y-2">
      {milestones.length === 0 && (
        <p className="text-sm text-slate-500">
          Aucun jalon : ce projet n&apos;annonce aucune date en dehors de sa mise en
          service.
        </p>
      )}

      {/* Two dates side by side are undecidable without being named: which
          one is announced and which one happened is the whole reading. The
          band takes the same widths as the rows below it. */}
      {milestones.length > 0 && (
        <div className="flex items-center gap-3 px-0 pb-1 text-xs text-slate-500">
          <span aria-hidden className="size-2 shrink-0" />
          <span className="min-w-0 flex-1">Nom</span>
          <span className="w-36 shrink-0">Date estimée</span>
          <span className="w-36 shrink-0">Date réalisée</span>
          {editable && <span aria-hidden className="size-6 shrink-0" />}
        </div>
      )}

      {milestones.length > 0 && (
        <ul className="divide-y divide-slate-200 border-y border-slate-200">
          {milestones.map((milestone) => {
            const late = isMilestoneLate(
              milestone.expected_on,
              milestone.reached_on,
              now,
            );
            return (
              <li key={milestone.id} className="flex items-center gap-3 py-1.5 text-sm">
                {/* Reached or not, in the shape the phases above already use:
                    filled is a fact, hollow is still to come, red is a day
                    gone by. The words beside the date carry it too. */}
                <span
                  aria-hidden
                  className={`size-2 shrink-0 rounded-full ${
                    milestone.reached_on
                      ? "bg-slate-600"
                      : late
                        ? "border border-red-500 bg-red-100"
                        : "border border-slate-400"
                  }`}
                />

                <span className="min-w-0 flex-1">
                  {editable ? (
                    <InlineTextField
                      value={milestone.label}
                      label={`Nom du jalon ${milestone.label}`}
                      onChange={(next) =>
                        onChange(milestone.id, { label: next ?? milestone.label })
                      }
                    />
                  ) : (
                    <span className="text-slate-700">{milestone.label}</span>
                  )}
                </span>

                <span className="w-36 shrink-0">
                  <InlineDateField
                    value={milestone.expected_on}
                    label={`Date estimée de ${milestone.label}`}
                    editable={editable}
                    late={late}
                    onChange={(next) =>
                      // The announced day is what a milestone is: a field
                      // emptied would leave a line nothing can sort, so the
                      // cross is not offered and a blank is ignored.
                      next ? onChange(milestone.id, { expected_on: next }) : undefined
                    }
                  />
                </span>

                <span className="w-36 shrink-0">
                  <InlineDateField
                    value={milestone.reached_on}
                    label={`Date réalisée de ${milestone.label}`}
                    editable={editable}
                    clearable
                    onChange={(next) => onChange(milestone.id, { reached_on: next })}
                  />
                </span>

                {editable && (
                  <button
                    type="button"
                    aria-label={`Retirer ${milestone.label}`}
                    title="Retirer ce jalon"
                    onClick={() => void onRemove(milestone.id)}
                    className="shrink-0 cursor-pointer rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                  >
                    <X className="size-4" aria-hidden />
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {/* Both fields at once: a milestone is a name and a day, and one
          without the other is refused by the domain anyway. */}
      {editable && (
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <input
            type="text"
            value={label}
            aria-label="Nom du jalon à ajouter"
            placeholder="Livraison du lot 1…"
            onChange={(event) => setLabel(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void post();
            }}
            className="min-w-0 flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-400 focus:outline-none"
          />
          <input
            type="date"
            value={expectedOn}
            aria-label="Date estimée du jalon"
            onChange={(event) => setExpectedOn(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void post();
            }}
            className="w-36 cursor-pointer rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-400 focus:outline-none"
          />
          <button
            type="button"
            disabled={!complete || posting}
            onClick={() => void post()}
            className="flex cursor-pointer items-center gap-1 rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Plus className="size-3 shrink-0 text-slate-400" aria-hidden />
            Ajouter le jalon
          </button>
        </div>
      )}
    </div>
  );
}
