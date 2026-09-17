"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

interface InlineNumberFieldProps {
  valeur: number | null | undefined;
  suffixe: string;
  invite: string;
  onChange: (valeur: number | null) => void | Promise<void>;
}

/**
 * Un nombre qui s'edite la ou il s'affiche.
 *
 * Le champ n'apparait qu'au clic : une fiche se lit bien plus souvent qu'elle
 * ne se modifie, et une bordure de saisie permanente ferait du bruit sur chaque
 * ligne.
 */
export function InlineNumberField({
  valeur,
  suffixe,
  invite,
  onChange,
}: InlineNumberFieldProps) {
  const [saisie, setSaisie] = useState<string | null>(null);

  function valider() {
    if (saisie === null) return;
    const propre = saisie.trim().replace(",", ".");
    setSaisie(null);
    const nombre = propre === "" ? null : Number(propre);
    if (nombre !== null && (Number.isNaN(nombre) || nombre < 0)) return;
    if (nombre !== (valeur ?? null)) void onChange(nombre);
  }

  if (saisie !== null) {
    return (
      <input
        type="text"
        inputMode="decimal"
        autoFocus
        value={saisie}
        aria-label={invite}
        onChange={(event) => setSaisie(event.target.value)}
        onBlur={valider}
        onKeyDown={(event) => {
          if (event.key === "Enter") valider();
          if (event.key === "Escape") setSaisie(null);
        }}
        className="w-24 rounded border border-slate-400 px-1.5 py-0.5 text-sm focus:outline-none"
      />
    );
  }

  return (
    <button
      type="button"
      aria-label={invite}
      onClick={() =>
        setSaisie(valeur === null || valeur === undefined ? "" : String(valeur))
      }
      className="-mx-1 cursor-pointer rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100"
    >
      {valeur === null || valeur === undefined ? (
        <span className="flex items-center gap-1 text-slate-400">
          <Plus className="size-3.5" aria-hidden />
          {invite}
        </span>
      ) : (
        <span className="text-slate-700">
          {valeur} {suffixe}
        </span>
      )}
    </button>
  );
}
