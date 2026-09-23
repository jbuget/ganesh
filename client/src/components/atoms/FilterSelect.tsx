"use client";

import { Check, ChevronDown, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { SEARCH_FIELD, SEARCH_ICON } from "@/lib/search-field";
import { normalise } from "@/lib/search-text";

export interface FilterOption {
  value: string;
  label: string;
  /** Dot or thumbnail shown before the label, if there is one. */
  thumbnail?: React.ReactNode;
  /**
   * The family the option belongs to, where the list is long enough to need
   * them. Options carrying one must arrive grouped: the heading is drawn
   * wherever the family changes, and a family coming back later would be
   * announced twice.
   */
  group?: string;
}

interface FilterSelectProps {
  label: string;
  options: FilterOption[];
  values: string[];
  onChange: (values: string[]) => void;
  /**
   * What the field searches, where the list is long enough to need one:
   * « Rechercher un collaborateur ». Its presence is what opens the field,
   * and it labels it — a placeholder is not a label, and a field named one
   * way to the eye and another to a screen reader is two fields.
   *
   * Left out, the list is read whole, which is right for a handful of
   * choices: a field above five options is furniture.
   */
  search?: string;
}

/**
 * A filter criterion with multiple choices.
 *
 * Each value toggles on click, with no confirmation and no closing: three get
 * ticked in a row without reopening the menu. The trigger announces how many
 * are kept, so the bar says what it filters once folded.
 *
 * A long list scrolls inside the panel rather than growing past the top of
 * the screen, and is read under the headings its options name — thirty
 * choices in one flat column is a column abandoned at the third line. Longer
 * still, or made of names, it is searched: `search` opens the field.
 *
 * Narrowing the list is a way of finding a value, never of unticking the ones
 * it hides: what was kept is kept, and the trigger goes on counting it.
 */
export function FilterSelect({
  label,
  options,
  values,
  onChange,
  search,
}: FilterSelectProps) {
  const [isOpen, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const chosen = new Set(values);

  const shown = useMemo(() => {
    const looked = normalise(typed.trim());
    if (looked === "") return options;
    return options.filter((option) => normalise(option.label).includes(looked));
  }, [options, typed]);

  function toggle(value: string) {
    const next = new Set(chosen);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    // The order of the options is what counts: two identical selections
    // produce the same address, whatever the order of the clicks.
    onChange(options.filter((o) => next.has(o.value)).map((o) => o.value));
  }

  return (
    <Popover
      open={isOpen}
      onOpenChange={(opening) => {
        setOpen(opening);
        // Closed and reopened, the panel shows the whole list again: what one
        // typed to find a name last time is not a question one is still
        // asking, and it would hide the list with no visible reason.
        if (!opening) setTyped("");
      }}
    >
      <PopoverTrigger
        className={`flex cursor-pointer items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm transition-colors ${
          values.length > 0
            ? "border-sky-300 bg-sky-50 text-sky-900"
            : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
        }`}
      >
        {label}
        {values.length > 0 && (
          <span className="rounded-full bg-sky-600 px-1.5 text-xs font-medium tabular-nums text-white">
            {values.length}
          </span>
        )}
        <ChevronDown className="size-3.5 shrink-0 opacity-60" aria-hidden />
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="max-h-[min(60vh,24rem)] w-72 overflow-y-auto p-1"
      >
        {search !== undefined && (
          <div className="relative mb-1">
            <Search className={SEARCH_ICON} aria-hidden />
            <Input
              type="search"
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              placeholder={search}
              aria-label={search}
              className={SEARCH_FIELD}
            />
          </div>
        )}

        {shown.length === 0 && (
          <p className="px-2 py-3 text-center text-sm text-slate-400">
            Aucun résultat.
          </p>
        )}

        <ul>
          {shown.map((option, rank) => {
            const kept = chosen.has(option.value);
            // Drawn where the family changes, and never above the first one:
            // a heading is what breaks a long list into readable stretches.
            // Read off what is shown rather than off every option: narrowed to
            // one family, the others' headings have nothing left under them.
            const opensFamily =
              option.group !== undefined && option.group !== shown[rank - 1]?.group;
            return (
              <li key={option.value}>
                {opensFamily && (
                  <p
                    className={`px-2 pb-1 text-xs font-medium text-slate-500 ${rank > 0 ? "mt-2 border-t border-slate-200 pt-2" : "pt-1"}`}
                  >
                    {option.group}
                  </p>
                )}
                <button
                  type="button"
                  aria-pressed={kept}
                  onClick={() => toggle(option.value)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                >
                  {option.thumbnail}
                  <span className="min-w-0 flex-1 truncate">{option.label}</span>
                  {kept && (
                    <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
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
