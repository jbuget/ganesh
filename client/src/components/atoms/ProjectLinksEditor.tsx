"use client";

import { ExternalLink, Plus, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProjectLinkResponse } from "@/lib/api/generated/model";

interface ProjectLinksEditorProps {
  liens: ProjectLinkResponse[];
  onAdd: (label: string, url: string) => Promise<void>;
  onRemove: (linkId: number) => Promise<void>;
}

/**
 * Liens utiles d'une mission.
 *
 * Le formulaire ne s'ouvre qu'a la demande : une fiche se consulte plus
 * souvent qu'elle ne se remplit, et deux champs vides en permanence
 * encombreraient la lecture.
 */
export function ProjectLinksEditor({
  liens,
  onAdd,
  onRemove,
}: ProjectLinksEditorProps) {
  const [ouvert, setOuvert] = useState(false);
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);

  async function ajouter() {
    setErreur(null);
    try {
      await onAdd(label, url);
      setLabel("");
      setUrl("");
      setOuvert(false);
    } catch {
      setErreur("Cette adresse n'est pas valide. Elle doit commencer par http://.");
    }
  }

  return (
    <div className="space-y-1.5">
      {liens.length === 0 && !ouvert && (
        <p className="text-sm text-slate-400">Aucun lien</p>
      )}

      <ul className="space-y-1">
        {liens.map((lien) => (
          <li key={lien.id} className="group flex items-center gap-1.5">
            <a
              href={lien.url}
              target="_blank"
              rel="noreferrer noopener"
              className="flex min-w-0 cursor-pointer items-center gap-1.5 text-sm text-sky-700 hover:underline"
            >
              <ExternalLink className="size-3.5 shrink-0" aria-hidden />
              <span className="truncate">{lien.label}</span>
            </a>
            <button
              type="button"
              aria-label={`Retirer ${lien.label}`}
              onClick={() => void onRemove(lien.id)}
              className="cursor-pointer rounded p-0.5 text-slate-300 opacity-0 transition hover:text-red-600 group-hover:opacity-100"
            >
              <X className="size-3.5" aria-hidden />
            </button>
          </li>
        ))}
      </ul>

      {ouvert ? (
        <div className="space-y-1.5 pt-1">
          <Input
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            placeholder="Intitulé (facultatif)"
            className="h-8 text-sm"
          />
          <Input
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://…"
            className="h-8 text-sm"
          />
          {erreur && <p className="text-xs text-red-700">{erreur}</p>}
          <div className="flex gap-2">
            <Button size="sm" onClick={() => void ajouter()} disabled={!url.trim()}>
              Ajouter
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setOuvert(false)}>
              Annuler
            </Button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setOuvert(true)}
          className="flex cursor-pointer items-center gap-1 text-sm text-slate-400 transition-colors hover:text-slate-600"
        >
          <Plus className="size-3.5" aria-hidden />
          Ajouter un lien
        </button>
      )}
    </div>
  );
}
