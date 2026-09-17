"use client";

import { Check, Sparkles, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { LinkIcon } from "@/lib/api/generated/model";
import { ICONES_DE_LIEN, dessinIcone } from "@/lib/link-icons";

interface LinkIconPickerProps {
  /** `null` : laisser l'adresse decider. */
  valeur: LinkIcon | null;
  onChange: (valeur: LinkIcon | null) => void;
}

/**
 * L'icone d'un lien.
 *
 * « Automatique » est propose en tete et reste le choix par defaut : coller une
 * adresse connue suffit le plus souvent, et c'est le serveur qui tranche. Le
 * selecteur n'est la que pour les cas ou il se tromperait.
 */
export function LinkIconPicker({ valeur, onChange }: LinkIconPickerProps) {
  const [ouvert, setOuvert] = useState(false);

  return (
    <Popover open={ouvert} onOpenChange={setOuvert}>
      <PopoverTrigger
        aria-label="Choisir l'icône du lien"
        className="flex h-8 w-9 cursor-pointer items-center justify-center rounded-md border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
      >
        <Glyphe Dessin={valeur ? dessinIcone(valeur) : Sparkles} />
      </PopoverTrigger>

      <PopoverContent align="start" className="w-52 p-1">
        <ul>
          <li>
            <Choix
              Dessin={Sparkles}
              libelle="Automatique"
              actif={valeur === null}
              onClick={() => {
                setOuvert(false);
                onChange(null);
              }}
            />
          </li>
          {ICONES_DE_LIEN.map((icone) => (
            <li key={icone.valeur}>
              <Choix
                Dessin={icone.Dessin}
                libelle={icone.libelle}
                actif={icone.valeur === valeur}
                onClick={() => {
                  setOuvert(false);
                  onChange(icone.valeur);
                }}
              />
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}

/** Le dessin d'une icone, recu en prop : rien n'est cree pendant le rendu. */
function Glyphe({ Dessin, className }: { Dessin: LucideIcon; className?: string }) {
  return <Dessin className={`size-4 shrink-0 ${className ?? ""}`} aria-hidden />;
}

function Choix({
  Dessin,
  libelle,
  actif,
  onClick,
}: {
  Dessin: LucideIcon;
  libelle: string;
  actif: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={actif}
      onClick={onClick}
      className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
    >
      <Glyphe Dessin={Dessin} className="text-slate-500" />
      <span className="min-w-0 flex-1 truncate">{libelle}</span>
      {actif && <Check className="size-4 shrink-0 text-sky-600" aria-hidden />}
    </button>
  );
}
