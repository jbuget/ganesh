"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface EditableTitleProps {
  label: string;
  /** Ce que le bouton crayon annonce aux lecteurs d'ecran. */
  invite: string;
  /** Absent quand le renommage n'est pas permis : le crayon disparait alors. */
  onRename?: (label: string) => void | Promise<void>;
  /** `1` en pleine page, `2` dans un panneau : le titre suit son contexte. */
  niveau?: 1 | 2;
}

/**
 * Un titre qui se renomme sur place.
 *
 * Le crayon n'ouvre le champ qu'a la demande : un titre se lit bien plus
 * souvent qu'il ne se change, et une bordure de saisie permanente ferait du
 * bruit en tete de chaque fiche. Une fois ouvert, le champ s'assume : boutons
 * explicites, Entree pour valider, Echap pour abandonner.
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
      // La saisie reste a l'ecran : on ne fait pas retaper un titre a quelqu'un
      // sous pretexte que le reseau a flanche.
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
              // Le panneau se ferme sur Echap : sans cela, abandonner la saisie
              // fermerait la fiche par la meme occasion.
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
