"use client";

import { Check, GitMerge } from "lucide-react";
import { useState } from "react";

import { InlineTextField } from "@/components/atoms/InlineTextField";
import { TagColorPicker } from "@/components/atoms/TagColorPicker";
import { TagMark } from "@/components/atoms/TagMark";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { TagColor, TagUsageResponse } from "@/lib/api/generated/model";
import { tagFailureSaid, tagNamesAlike } from "@/lib/tags";

interface TagManagerRowProps {
  tag: TagUsageResponse;
  /** The tags this one could be folded into: every tag in use but itself. */
  others: TagUsageResponse[];
  onRename: (name: string) => Promise<void>;
  onRecolor: (color: TagColor) => Promise<void>;
  /** Folds the tag into `targetId`: it is gone afterwards. */
  onMerge: (targetId: number) => Promise<void>;
}

/**
 * One tag of the vocabulary, for a manager to look after.
 *
 * Renaming, recolouring and folding all move every project carrying the tag,
 * so folding — the one that cannot be taken back — asks to be confirmed on the
 * line itself, naming both ends: « Suez Env » into « Suez », and not the other
 * way round.
 */
export function TagManagerRow({
  tag,
  others,
  onRename,
  onRecolor,
  onMerge,
}: TagManagerRowProps) {
  const [folding, setFolding] = useState<TagUsageResponse | null>(null);
  const [isPicking, setPicking] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  async function attempt(action: () => Promise<void>) {
    try {
      await action();
      setFailure(null);
    } catch (error) {
      setFailure(tagFailureSaid(error));
    }
  }

  /** What an inline field says before asking the server: a name already taken. */
  function takenName(name: string | null): string | null {
    if (name !== null && others.some((other) => tagNamesAlike(other.name, name))) {
      return "Un tag porte déjà ce nom : fusionnez-les plutôt.";
    }
    return null;
  }

  return (
    <li className="space-y-1 py-2">
      <div className="flex items-center gap-2">
        <TagColorPicker
          value={tag.color}
          label={`Couleur du tag ${tag.name}`}
          onChange={(color) => void attempt(() => onRecolor(color))}
        />

        <div className="min-w-0 flex-1">
          <InlineTextField
            value={tag.name}
            label={`Nom du tag ${tag.name}`}
            validate={takenName}
            onChange={async (name) => {
              if (name !== null) await onRename(name);
            }}
          />
        </div>

        <span className="shrink-0 text-xs text-slate-400">
          {tag.project_count} projet{tag.project_count > 1 ? "s" : ""}
        </span>

        {others.length > 0 && (
          <Popover open={isPicking} onOpenChange={setPicking}>
            <PopoverTrigger
              aria-label={`Fusionner ${tag.name} dans…`}
              title="Fusionner dans un autre tag"
              className="cursor-pointer rounded p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
            >
              <GitMerge className="size-4" aria-hidden />
            </PopoverTrigger>

            <PopoverContent align="end" className="w-56 gap-0 p-1">
              <p className="px-2 py-1.5 text-xs text-muted-foreground">
                Fusionner dans…
              </p>
              <ul className="max-h-56 overflow-y-auto overscroll-contain">
                {others.map((other) => (
                  <li key={other.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setFolding(other);
                        setPicking(false);
                      }}
                      className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                    >
                      <TagMark tag={other} />
                    </button>
                  </li>
                ))}
              </ul>
            </PopoverContent>
          </Popover>
        )}
      </div>

      {folding && (
        <div className="flex flex-wrap items-center gap-2 rounded bg-amber-50 px-2 py-1.5 text-sm text-amber-900">
          <span className="min-w-0 flex-1">
            Fusionner « {tag.name} » dans « {folding.name} » ? Les projets qui portent «{" "}
            {tag.name} » porteront « {folding.name} », et « {tag.name} » disparaîtra.
          </span>
          <button
            type="button"
            onClick={() => {
              const target = folding;
              setFolding(null);
              void attempt(() => onMerge(target.id));
            }}
            className="flex cursor-pointer items-center gap-1 rounded bg-amber-600 px-2 py-1 text-xs font-medium text-white transition-colors hover:bg-amber-700"
            aria-label="Confirmer la fusion"
          >
            <Check className="size-3.5" aria-hidden />
            Fusionner
          </button>
          <button
            type="button"
            onClick={() => setFolding(null)}
            className="cursor-pointer rounded px-2 py-1 text-xs text-amber-900 transition-colors hover:bg-amber-100"
          >
            Annuler
          </button>
        </div>
      )}

      {failure && (
        <p role="alert" className="text-xs text-red-600">
          {failure}
        </p>
      )}
    </li>
  );
}
