"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";

import { LinkIconPicker } from "@/components/atoms/LinkIconPicker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { LinkIcon, ProjectLinkResponse } from "@/lib/api/generated/model";
import { dessinIcone, libelleIcone } from "@/lib/link-icons";

interface ProjectLinksEditorProps {
  liens: ProjectLinkResponse[];
  /** `icone` a `null` : l'adresse decide, cote serveur. */
  onAdd: (label: string, url: string, icone: LinkIcon | null) => Promise<void>;
  onRemove: (linkId: number) => Promise<void>;
}

/**
 * Les liens utiles d'une mission : autant qu'on veut, chacun avec son icone.
 *
 * La saisie vit dans un popover ancre au bouton, comme les autres champs de la
 * fiche : les liens restent une valeur parmi d'autres, et la fiche ne disparait
 * pas derriere un voile pour trois champs.
 */
export function ProjectLinksEditor({
  liens,
  onAdd,
  onRemove,
}: ProjectLinksEditorProps) {
  const [ouvert, setOuvert] = useState(false);
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [icone, setIcone] = useState<LinkIcon | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  function changerOuverture(valeur: boolean) {
    setOuvert(valeur);
    // Refermer, de quelque maniere que ce soit, remet le formulaire a neuf.
    if (!valeur) {
      setLabel("");
      setUrl("");
      setIcone(null);
      setErreur(null);
    }
  }

  async function ajouter() {
    setErreur(null);
    try {
      await onAdd(label, url, icone);
      changerOuverture(false);
    } catch {
      setErreur("Cette adresse n'est pas valide. Elle doit commencer par http://.");
    }
  }

  return (
    <div className="space-y-1">
      <ul className="space-y-1">
        {liens.map((lien) => {
          const Dessin = dessinIcone(lien.icone);
          return (
            <li key={lien.id} className="flex items-center gap-1.5">
              <a
                href={lien.url}
                target="_blank"
                rel="noreferrer noopener"
                className="flex min-w-0 cursor-pointer items-center gap-1.5 text-sm text-sky-700 hover:underline"
              >
                <Dessin
                  className="size-3.5 shrink-0"
                  aria-label={libelleIcone(lien.icone)}
                />
                <span className="truncate">{lien.label}</span>
              </a>
              <button
                type="button"
                aria-label={`Retirer ${lien.label}`}
                onClick={() => void onRemove(lien.id)}
                // Toujours visible, et pas seulement au survol : la croix doit
                // s'atteindre au doigt comme a la souris.
                className="cursor-pointer rounded p-0.5 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
              >
                <X className="size-3.5" aria-hidden />
              </button>
            </li>
          );
        })}
      </ul>

      <Popover open={ouvert} onOpenChange={changerOuverture}>
        <PopoverTrigger className="flex cursor-pointer items-center gap-1 text-sm text-slate-400 transition-colors hover:text-slate-600">
          <Plus className="size-3.5" aria-hidden />
          Ajouter un lien
        </PopoverTrigger>

        <PopoverContent align="start" className="w-80 gap-1.5">
          <div className="flex gap-1.5">
            <LinkIconPicker valeur={icone} onChange={setIcone} />
            <Input
              value={label}
              onChange={(event) => setLabel(event.target.value)}
              placeholder="Intitulé (facultatif)"
              className="h-8 text-sm"
            />
          </div>
          <Input
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://…"
            className="h-8 text-sm"
            onKeyDown={(event) => {
              if (event.key === "Enter" && url.trim()) void ajouter();
            }}
          />
          {erreur && <p className="text-xs text-red-700">{erreur}</p>}
          <div className="flex gap-2">
            <Button size="sm" onClick={() => void ajouter()} disabled={!url.trim()}>
              Ajouter
            </Button>
            <Button size="sm" variant="ghost" onClick={() => changerOuverture(false)}>
              Annuler
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
