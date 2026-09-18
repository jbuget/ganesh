"use client";

import { Check, Sparkles, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { LinkIcon } from "@/lib/api/generated/model";
import { LINK_ICONS, iconGlyph } from "@/lib/link-icons";

interface LinkIconPickerProps {
  /** `null` : laisser l'adresse decider. */
  value: LinkIcon | null;
  onChange: (value: LinkIcon | null) => void;
}

/**
 * The icon of a link.
 *
 * \u00ab Automatique \u00bb comes first and stays the default: pasting a known
 * address is usually enough, and the server decides. The picker is only there
 * for the cases where it would get it wrong.
 */
export function LinkIconPicker({ value, onChange }: LinkIconPickerProps) {
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Choisir l'icône du lien"
        className="flex h-8 w-9 cursor-pointer items-center justify-center rounded-md border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
      >
        <Glyph icon={value ? iconGlyph(value) : Sparkles} />
      </PopoverTrigger>

      <PopoverContent align="start" className="w-52 p-1">
        <ul>
          <li>
            <Choice
              icon={Sparkles}
              label="Automatique"
              is_active={value === null}
              onClick={() => {
                setOpen(false);
                onChange(null);
              }}
            />
          </li>
          {LINK_ICONS.map((icon) => (
            <li key={icon.value}>
              <Choice
                icon={icon.glyph}
                label={icon.label}
                is_active={icon.value === value}
                onClick={() => {
                  setOpen(false);
                  onChange(icon.value);
                }}
              />
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}

/** An icon drawing, received as a prop: nothing is created during the render. */
function Glyph({ icon: Icon, className }: { icon: LucideIcon; className?: string }) {
  return <Icon className={`size-4 shrink-0 ${className ?? ""}`} aria-hidden />;
}

function Choice({
  icon,
  label,
  is_active,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  is_active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={is_active}
      onClick={onClick}
      className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
    >
      <Glyph icon={icon} className="text-slate-500" />
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {is_active && <Check className="size-4 shrink-0 text-sky-600" aria-hidden />}
    </button>
  );
}
