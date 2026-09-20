"use client";

import { Check, ChevronDown, History } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { DigestVersionResponse } from "@/lib/api/generated/model";
import { versionLabel } from "@/lib/gazette";

interface DigestVersionPickerProps {
  versions: DigestVersionResponse[];
  /** Which one is on screen. */
  current: number;
  onOpen: (version: number) => void;
}

/**
 * The generations of a month, and which one is being read.
 *
 * A month is read as its latest, and the others are never thrown away: a
 * figure somebody quoted from a digest has to still be in the digest they
 * quoted it from. Only shown once there is more than one — a picker offering
 * a single choice is furniture.
 */
export function DigestVersionPicker({
  versions,
  current,
  onOpen,
}: DigestVersionPickerProps) {
  const [isOpen, setOpen] = useState(false);
  if (versions.length < 2) return null;

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Version affichée : ${current}`}
        className="flex cursor-pointer items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-700 transition-colors hover:border-slate-400"
      >
        <History className="size-3.5 shrink-0 opacity-60" aria-hidden />
        <span>Version {current}</span>
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="end" className="w-80 p-1">
        <ul role="listbox" aria-label="Versions du digest">
          {versions.map((version) => {
            const isCurrent = version.version === current;
            return (
              <li key={version.version} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={isCurrent}
                  onClick={() => {
                    setOpen(false);
                    if (!isCurrent) onOpen(version.version);
                  }}
                  className="flex w-full cursor-pointer items-start gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate">
                      {versionLabel(version.version, version.generated_at)}
                    </span>
                    <span className="block truncate text-xs text-slate-500">
                      Demandé par {version.requested_by}
                    </span>
                  </span>
                  {isCurrent && (
                    <Check
                      className="mt-0.5 size-4 shrink-0 text-sky-600"
                      aria-hidden
                    />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
