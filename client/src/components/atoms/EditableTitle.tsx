"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface EditableTitleProps {
  label: string;
  /** What the pencil button announces to screen readers. */
  invite: string;
  /** Absent when renaming is not allowed: the pencil then disappears. */
  onRename?: (label: string) => void | Promise<void>;
  /** `1` on a full page, `2` in a panel: the title follows its context. */
  niveau?: 1 | 2;
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
  invite,
  onRename,
  niveau = 2,
}: EditableTitleProps) {
  const [entry, setSaisie] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [hasError, setEnErreur] = useState(false);

  const propre = entry?.trim() ?? "";
  const valide = propre.length > 0;

  function abandonner() {
    setSaisie(null);
    setEnErreur(false);
  }

  async function valider() {
    if (!valide || enCours) return;
    if (propre === label) {
      abandonner();
      return;
    }
    setEnCours(true);
    setEnErreur(false);
    try {
      await onRename?.(propre);
      abandonner();
    } catch {
      // The input stays on screen: nobody is made to retype a title because
      // the network gave out.
      setEnErreur(true);
    } finally {
      setEnCours(false);
    }
  }

  if (entry !== null) {
    return (
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Input
            autoFocus
            value={entry}
            disabled={enCours}
            aria-label={invite}
            aria-invalid={hasError || undefined}
            onChange={(event) => setSaisie(event.target.value)}
            onKeyDown={(event) => {
              // The panel closes on Escape: without this, giving up on the
              // input would close the sheet at the same time.
              if (event.key === "Escape") {
                event.stopPropagation();
                abandonner();
              }
              if (event.key === "Enter") void valider();
            }}
            className="text-sm"
          />

          <Button
            size="sm"
            variant="ghost"
            disabled={enCours}
            onClick={abandonner}
            className="cursor-pointer"
          >
            Annuler
          </Button>
          <Button
            size="sm"
            disabled={!valide || enCours}
            onClick={() => void valider()}
            className="cursor-pointer"
          >
            Enregistrer
          </Button>
        </div>

        {hasError && (
          <p role="alert" className="mt-1 text-xs text-red-700">
            Le nouveau titre n&apos;a pas pu être enregistré.
          </p>
        )}
      </div>
    );
  }

  const Titre = niveau === 1 ? "h1" : "h2";

  return (
    <div className="flex min-w-0 flex-1 items-center gap-1.5">
      <Titre
        className={`truncate font-semibold ${niveau === 1 ? "text-xl" : "text-base"}`}
      >
        {label}
      </Titre>

      {onRename && (
        <button
          type="button"
          aria-label={invite}
          onClick={() => setSaisie(label)}
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <Pencil className="size-3.5" aria-hidden />
        </button>
      )}
    </div>
  );
}
