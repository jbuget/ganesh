"use client";

import { Archive, Plus, RotateCcw } from "lucide-react";
import { useState } from "react";

import { InlineNumberField } from "@/components/atoms/InlineNumberField";
import { InlineTextField } from "@/components/atoms/InlineTextField";
import { WithdrawActivityDialog } from "@/components/atoms/WithdrawActivityDialog";
import type { ActivityResponse, WorkNature } from "@/lib/api/generated/model";
import { WORK_NATURES, workNatureLabel } from "@/lib/work-natures";

interface ProjectActivitiesProps {
  activities: ActivityResponse[];
  /**
   * Whether the reader may change what the mission is cut into.
   *
   * A guest reads the application whole and declares nothing into it: the
   * gestures are simply not offered, the API refusing them anyway.
   */
  editable: boolean;
  onAdd: (label: string, nature: WorkNature | null) => void | Promise<void>;
  onChange: (
    activityId: number,
    fields: { label?: string; estimated_days?: number | null },
  ) => void | Promise<void>;
  onArchive: (activityId: number) => void | Promise<void>;
  /** Only ever called on an activity nobody declared on. */
  onRemove: (activityId: number) => void | Promise<void>;
  onUnarchive: (activityId: number) => void | Promise<void>;
}

/**
 * The trades a mission is cut into, and what each is budgeted at.
 *
 * A mission carrying no activity cannot be declared on at all, which is why
 * the section says so plainly rather than showing an empty list: somebody
 * looking at a grid that offers them nothing has to be told where to go.
 *
 * The budget lives here rather than on the mission: an estimate counted in
 * build days stops meaning anything the moment the days of every trade are
 * taken off it. The mission reads the sum, and reads nothing while one of
 * them is left blank — which the section says too.
 */
/** What withdrawing an activity leaves behind, said before it happens. */
function booked(activity: ActivityResponse): string {
  const days = activity.entries ?? 0;
  if (days === 0) return "Retirer des activités déclarables";
  return `${days} saisie${days > 1 ? "s" : ""} restent lisibles`;
}

export function ProjectActivities({
  activities,
  onAdd,
  onChange,
  editable,
  onArchive,
  onRemove,
  onUnarchive,
}: ProjectActivitiesProps) {
  const [adding, setAdding] = useState<WorkNature | null>(null);
  const [withdrawing, setWithdrawing] = useState<ActivityResponse | null>(null);

  const live = activities.filter((activity) => activity.is_active);
  // A trade is one thing per mission: two « Développement » would split the
  // budget across two lines nobody can tell apart. Offered greyed rather than
  // hidden, so the list of trades stays the same list from one mission to the
  // next and one can see at a glance what is already covered.
  const taken = new Set(live.map((activity) => activity.nature));
  const archived = activities.filter((activity) => !activity.is_active);
  const unbudgeted = live.filter((activity) => activity.estimated_days === null);

  return (
    <div className="space-y-2">
      {live.length === 0 && (
        <p className="text-sm text-slate-500">
          Aucune activité : personne ne peut déclarer de temps sur ce projet tant
          qu&apos;il n&apos;en porte pas au moins une.
        </p>
      )}

      {live.length > 0 && (
        <ul className="divide-y divide-slate-200 border-y border-slate-200">
          {live.map((activity) => (
            <li key={activity.id} className="flex items-center gap-3 py-1.5 text-sm">
              <span className="min-w-0 flex-1">
                <InlineTextField
                  value={activity.label}
                  label="Nom de l'activité"
                  onChange={(label) =>
                    onChange(activity.id, { label: label ?? activity.label })
                  }
                />
              </span>

              <span className="w-40 shrink-0 text-slate-500">
                {workNatureLabel(activity.nature) ?? "Métier non précisé"}
              </span>

              <span className="w-28 shrink-0">
                <InlineNumberField
                  value={activity.estimated_days}
                  suffix="jrs."
                  label="Estimer"
                  onChange={(estimated_days) =>
                    onChange(activity.id, { estimated_days })
                  }
                />
              </span>

              <button
                type="button"
                aria-label={`Retirer ${activity.label}`}
                title={booked(activity)}
                disabled={!editable}
                onClick={() => setWithdrawing(activity)}
                className="shrink-0 cursor-pointer rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
              >
                <Archive className="size-4" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}

      {unbudgeted.length > 0 && live.length > 0 && (
        <p className="text-xs text-amber-700">
          {unbudgeted.length > 1
            ? `${unbudgeted.length} activités n’ont pas d’estimé`
            : "Une activité n’a pas d’estimé"}{" "}
          : tant qu&apos;il en manque un, le projet n&apos;affiche pas de ratio.
        </p>
      )}

      {/* Adding names the trade first: it is the one thing that cannot be
          filled in afterwards without somebody deciding what it was. */}
      <div className="flex flex-wrap items-center gap-1.5 pt-1">
        {WORK_NATURES.map((nature) => (
          <button
            key={nature.value}
            type="button"
            disabled={!editable || adding !== null || taken.has(nature.value)}
            onClick={async () => {
              setAdding(nature.value);
              await onAdd(nature.label, nature.value);
              setAdding(null);
            }}
            title={
              taken.has(nature.value)
                ? `Ce projet porte déjà une activité de ${nature.label}`
                : undefined
            }
            className="flex cursor-pointer items-center gap-1 rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Plus className="size-3 shrink-0 text-slate-400" aria-hidden />
            {nature.label}
          </button>
        ))}
      </div>

      {withdrawing && (
        <WithdrawActivityDialog
          open
          onOpenChange={(isOpen) => !isOpen && setWithdrawing(null)}
          label={withdrawing.label}
          entries={withdrawing.entries ?? 0}
          onConfirm={async () => {
            // Deleted when it carries nothing, archived when it does: the
            // API refuses the other way round, and the dialog has already
            // said which of the two this is.
            await ((withdrawing.entries ?? 0) > 0
              ? onArchive(withdrawing.id)
              : onRemove(withdrawing.id));
            setWithdrawing(null);
          }}
        />
      )}

      {archived.length > 0 && (
        <details className="pt-1">
          <summary className="cursor-pointer text-xs text-slate-500">
            {archived.length > 1
              ? `${archived.length} activités archivées`
              : "1 activité archivée"}
          </summary>
          <ul className="mt-1 space-y-1">
            {archived.map((activity) => (
              <li
                key={activity.id}
                className="flex items-center gap-2 text-sm text-slate-500"
              >
                <span className="min-w-0 flex-1 truncate">{activity.label}</span>
                <button
                  type="button"
                  aria-label={`Rouvrir ${activity.label}`}
                  onClick={() => void onUnarchive(activity.id)}
                  className="shrink-0 cursor-pointer rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                >
                  <RotateCcw className="size-4" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
