"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";

import { LinkIconPicker } from "@/components/atoms/LinkIconPicker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { LinkIcon, ProjectLinkResponse } from "@/lib/api/generated/model";
import { iconGlyph, iconLabel } from "@/lib/link-icons";

interface ProjectLinksEditorProps {
  links: ProjectLinkResponse[];
  /** `icone` a `null` : l'adresse decide, cote serveur. */
  onAdd: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  onRemove: (linkId: number) => Promise<void>;
  /**
   * Whether the reader may add or withdraw a link.
   *
   * The links themselves always open: they are the addresses of the service,
   * and reading a sheet means following them.
   */
  editable?: boolean;
}

/**
 * A mission's useful links: as many as wanted, each with its icon.
 *
 * Input lives in a popover anchored to the button, like the other fields of the
 * sheet: links stay one value among others, and the sheet does not vanish
 * behind a veil for three fields.
 */
export function ProjectLinksEditor({
  links,
  editable = true,
  onAdd,
  onRemove,
}: ProjectLinksEditorProps) {
  const [isOpen, setOpen] = useState(false);
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [icon, setIcon] = useState<LinkIcon | null>(null);
  const [error, setError] = useState<string | null>(null);

  function toggleExpanded(value: boolean) {
    setOpen(value);
    // Closing, in any way at all, resets the form.
    if (!value) {
      setLabel("");
      setUrl("");
      setIcon(null);
      setError(null);
    }
  }

  async function add() {
    setError(null);
    try {
      await onAdd(label, url, icon);
      toggleExpanded(false);
    } catch {
      setError("Cette adresse n'est pas valide. Elle doit commencer par http://.");
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
                  aria-label={iconLabel(link.icon)}
                />
                <span className="truncate">{link.label}</span>
              </a>
              {editable && (
                <button
                  type="button"
                  aria-label={`Retirer ${link.label}`}
                  onClick={() => void onRemove(link.id)}
                  // Always visible, and not only on hover: the cross must be
                  // reachable by finger as well as by mouse.
                  className="cursor-pointer rounded p-0.5 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <X className="size-3.5" aria-hidden />
                </button>
              )}
            </li>
          );
        })}
      </ul>

      {editable && (
        <Popover open={isOpen} onOpenChange={toggleExpanded}>
          <PopoverTrigger className="flex cursor-pointer items-center gap-1 text-sm text-slate-400 transition-colors hover:text-slate-600">
            <Plus className="size-3.5" aria-hidden />
            Ajouter un lien
          </PopoverTrigger>

          <PopoverContent align="start" className="w-80 gap-1.5">
            <div className="flex gap-1.5">
              <LinkIconPicker value={icon} onChange={setIcon} />
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
                if (event.key === "Enter" && url.trim()) void add();
              }}
            />
            {error && <p className="text-xs text-red-700">{error}</p>}
            <div className="flex gap-2">
              <Button size="sm" onClick={() => void add()} disabled={!url.trim()}>
                Ajouter
              </Button>
              <Button size="sm" variant="ghost" onClick={() => toggleExpanded(false)}>
                Annuler
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}
