"use client";

import { phaseDot, phaseLabel } from "@/lib/board";
import type { Destination } from "@/lib/command-palette";
import { since } from "@/lib/relative-dates";

interface CommandPaletteRowProps {
  destination: Destination;
  /** Whether the selection is standing on it, by arrow or by mouse. */
  selected: boolean;
  /** Frozen by the palette: every row of one drawing dates from the same now. */
  now: Date;
  onOpen: () => void;
  onHover: () => void;
}

/**
 * One line of the palette: a mark, a name, and what is known of it.
 *
 * The mark follows the grammar of the whole application — a screen carries its
 * own icon, a project the round dot of its phase, in the colour that phase
 * carries everywhere else.
 */
export function CommandPaletteRow({
  destination,
  selected,
  now,
  onOpen,
  onHover,
}: CommandPaletteRowProps) {
  // What moved it and when come before what it belongs to: a line of the
  // recent section is read for the first two, and the third only tells two
  // close names apart.
  const said = [
    destination.gesture,
    destination.at && since(destination.at, now),
    destination.hint,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <li
      id={destination.key}
      role="option"
      aria-selected={selected}
      data-active={selected}
      title={destination.label}
      onClick={onOpen}
      onMouseMove={onHover}
      className={[
        "flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-2 text-sm",
        selected ? "bg-slate-100" : "",
      ].join(" ")}
    >
      <span className="flex size-4 shrink-0 items-center justify-center">
        {destination.Icon ? (
          <destination.Icon className="size-4 text-slate-400" aria-hidden />
        ) : (
          <span
            aria-hidden
            title={destination.status ? phaseLabel(destination.status) : undefined}
            className={`size-2.5 rounded-full ${
              destination.status ? phaseDot(destination.status) : "bg-slate-300"
            }`}
          />
        )}
      </span>

      <span className="min-w-0 flex-1 truncate">{destination.label}</span>

      {/* Capped, and cut before the name is: a package's parent takes a whole
          line of its own, and what one typed was the name. */}
      {said && (
        <span className="min-w-0 max-w-[40%] truncate text-xs text-slate-400">
          {said}
        </span>
      )}
    </li>
  );
}
