"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface EditableTitleProps {
  label: string;
  /** What the pencil button announces to screen readers. */
  hint: string;
  /** Absent when renaming is not allowed: the pencil then disappears. */
  onRename?: (label: string) => void | Promise<void>;
  /** `1` on a full page, `2` in a panel: the title follows its context. */
  level?: 1 | 2;
}

/**
 * A title that renames in place.
 *
 * The pencil only opens the field on demand: a title is read far more often
 * than it is changed, and a permanent input border would make noise at the top
 * of every sheet. Once open, the field owns it: explicit buttons, Enter to
 * confirm, Escape to give up.
 */
export function EditableTitle({
  label,
  hint,
  onRename,
  level = 2,
}: EditableTitleProps) {
  const [entry, setEntry] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hasError, setHasError] = useState(false);

  const trimmed = entry?.trim() ?? "";
  const isValid = trimmed.length > 0;

  function cancel() {
    setEntry(null);
    setHasError(false);
  }

  async function validate() {
    if (!isValid || busy) return;
    if (trimmed === label) {
      cancel();
      return;
    }
    setBusy(true);
    setHasError(false);
    try {
      await onRename?.(trimmed);
      cancel();
    } catch {
      // The input stays on screen: nobody is made to retype a title because
      // the network gave out.
      setHasError(true);
    } finally {
      setBusy(false);
    }
  }

  if (entry !== null) {
    return (
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Input
            autoFocus
            value={entry}
            disabled={busy}
            aria-label={hint}
            aria-invalid={hasError || undefined}
            onChange={(event) => setEntry(event.target.value)}
            onKeyDown={(event) => {
              // The panel closes on Escape: without this, giving up on the
              // input would close the sheet at the same time.
              if (event.key === "Escape") {
                event.stopPropagation();
                cancel();
              }
              if (event.key === "Enter") void validate();
            }}
            className="text-sm"
          />

          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            onClick={cancel}
            className="cursor-pointer"
          >
            Annuler
          </Button>
          <Button
            size="sm"
            disabled={!isValid || busy}
            onClick={() => void validate()}
            className="cursor-pointer"
          >
            Enregistrer
          </Button>
        </div>

        {hasError && (
          <p role="alert" className="mt-1 text-xs text-red-700">
            Le nouveau title n&apos;a pas pu être enregistré.
          </p>
        )}
      </div>
    );
  }

  const Title = level === 1 ? "h1" : "h2";

  return (
    <div className="flex min-w-0 flex-1 items-center gap-1.5">
      <Title
        className={`truncate font-semibold ${level === 1 ? "text-xl" : "text-base"}`}
      >
        {label}
      </Title>

      {onRename && (
        <button
          type="button"
          aria-label={hint}
          onClick={() => setEntry(label)}
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <Pencil className="size-3.5" aria-hidden />
        </button>
      )}
    </div>
  );
}
