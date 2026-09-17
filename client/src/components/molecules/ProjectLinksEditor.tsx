"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";

import { LinkIconPicker } from "@/components/atoms/LinkIconPicker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { LinkIcon, ProjectLinkResponse } from "@/lib/api/generated/model";
import { iconGlyph, libelleIcone } from "@/lib/link-icons";

interface ProjectLinksEditorProps {
  links: ProjectLinkResponse[];
  /** `icone` a `null` : l'adresse decide, cote serveur. */
  onAdd: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
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
  links,
  onAdd,
  onRemove,
}: ProjectLinksEditorProps) {
  const [ouvert, setOuvert] = useState(false);
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [icon, setIcone] = useState<LinkIcon | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  function changerOuverture(value: boolean) {
    setOuvert(value);
    // Refermer, de quelque maniere que ce soit, remet le formulaire a neuf.
    if (!value) {
      setLabel("");
      setUrl("");
      setIcone(null);
      setErreur(null);
    }
  }

  async function ajouter() {
    setErreur(null);
    try {
      await onAdd(label, url, icon);
      changerOuverture(false);
    } catch {
      setErreur("Cette adresse n'est pas valide. Elle doit commencer par http://.");
    }
  }

  return (
    <div className="space-y-1">
      <ul className="space-y-1">
        {links.map((link) => {
          const Glyph = iconGlyph(link.icon);
          return (
            <li key={link.id} className="flex items-center gap-1.5">
              <a
                href={link.url}
                target="_blank"
                rel="noreferrer noopener"
                className="flex min-w-0 cursor-pointer items-center gap-1.5 text-sm text-slate-900 hover:underline"
              >
                <Glyph
                  className="size-3.5 shrink-0"
                  aria-label={libelleIcone(link.icon)}
                />
                <span className="truncate">{link.label}</span>
              </a>
              <button
                type="button"
                aria-label={`Retirer ${link.label}`}
                onClick={() => void onRemove(link.id)}
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
            <LinkIconPicker value={icon} onChange={setIcone} />
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
