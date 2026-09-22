"use client";

import { Check, Plus, Search } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useComboboxFilter } from "@/components/ui/combobox";
import { useRequestSponsors } from "@/lib/api/queries";

interface SponsorsPickerProps {
  values: number[];
  onChange: (values: number[]) => void | Promise<void>;
  /** False on a request nobody may rewrite any more. */
  editable?: boolean;
}

/**
 * The members of the COMEX a need is carried to.
 *
 * Several are possible: a need crossing two perimeters is carried by both,
 * and naming only one of them would make the other wonder why it arrived.
 *
 * The list is the sponsors' route rather than the team's: whoever files a
 * need reaches no list of teammates.
 */
export function SponsorsPicker({
  values,
  onChange,
  editable = true,
}: SponsorsPickerProps) {
  const { sponsors } = useRequestSponsors();
  const [isOpen, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { contains } = useComboboxFilter();
  const chosen = new Set(values);

  const named = sponsors.filter((sponsor) => chosen.has(sponsor.id));
  const proposes = sponsors.filter((sponsor) => contains(sponsor.label, search));

  function toggle(id: number) {
    const next = new Set(chosen);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    void onChange(sponsors.filter((s) => next.has(s.id)).map((s) => s.id));
  }

  const labels = (
    <>
      {named.map((sponsor) => (
        <span
          key={sponsor.id}
          className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700"
        >
          {sponsor.label}
        </span>
      ))}
    </>
  );

  if (!editable) {
    return named.length === 0 ? (
      <span className="text-sm text-slate-400">Non renseigné</span>
    ) : (
      <span className="flex flex-wrap items-center gap-1">{labels}</span>
    );
  }

  return (
    <Popover
      open={isOpen}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setSearch("");
      }}
    >
      <PopoverTrigger
        aria-label="Modifier les sponsors"
        className="-mx-1 flex cursor-pointer flex-wrap items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
      >
        {named.length === 0 ? (
          <span className="flex items-center gap-1 text-sm text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            Sponsors
          </span>
        ) : (
          labels
        )}
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 gap-0 p-1">
        {/* Negative margins: the popover has padding of its own, otherwise the
            rule under the field would stop short of the edges. */}
        <div className="-mx-1 flex items-center gap-2 border-b border-border px-2.5">
          <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <input
            type="text"
            autoFocus
            value={search}
            aria-label="Rechercher un sponsor"
            placeholder="Rechercher…"
            onChange={(event) => setSearch(event.target.value)}
            className="h-8 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </div>

        {proposes.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Aucun membre du COMEX ne correspond.
          </p>
        ) : (
          <ul className="max-h-64 overflow-y-auto overscroll-contain pt-1">
            {proposes.map((sponsor) => {
              const present = chosen.has(sponsor.id);
              return (
                <li key={sponsor.id}>
                  <button
                    type="button"
                    aria-pressed={present}
                    onClick={() => toggle(sponsor.id)}
                    className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                  >
                    <span className="min-w-0 flex-1 truncate">{sponsor.label}</span>
                    {present && (
                      <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </PopoverContent>
    </Popover>
  );
}
