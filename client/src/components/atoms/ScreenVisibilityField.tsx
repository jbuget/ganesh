"use client";

import type { NavBand } from "@/lib/navigation";

interface ScreenVisibilityFieldProps {
  /** The screens one may take off the bar, banded as the bar is. */
  bands: readonly NavBand[];
  /** The paths currently kept off the bar. */
  hidden: readonly string[];
  /** Says the whole list, so emptying it is the same gesture as filling it. */
  onChange: (hidden: string[]) => void;
  /** True while the choice is on its way to the API. */
  isSaving?: boolean;
}

/**
 * Which screens the bar shows: a checkbox per screen, checked while it is.
 *
 * Checked means shown. Ticking off is the gesture of taking something away, so
 * the box reads the way the bar does — what is on it — rather than asking
 * somebody to tick « masquer » forty times over.
 *
 * Grouped under the bar's own band headings, so what one reads here is what
 * one will find there.
 */
export function ScreenVisibilityField({
  bands,
  hidden,
  onChange,
  isSaving = false,
}: ScreenVisibilityFieldProps) {
  const toggle = (href: string, willShow: boolean) =>
    onChange(willShow ? hidden.filter((h) => h !== href) : [...hidden, href]);

  return (
    <fieldset disabled={isSaving} className="min-w-0">
      <legend className="sr-only">Pages affichées dans la barre latérale</legend>

      <div className="flex flex-col gap-4">
        {bands.map(({ band, label, screens }) => (
          <div key={band} className="flex flex-col gap-1">
            {label && (
              <p className="text-[11px] font-medium tracking-wide text-slate-400 uppercase">
                {label}
              </p>
            )}
            {screens.map(({ href, label: name, Icon }) => {
              const isShown = !hidden.includes(href);
              return (
                <label
                  key={href}
                  className={[
                    "flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 text-sm hover:bg-slate-50",
                    isSaving ? "cursor-progress opacity-60" : "",
                  ].join(" ")}
                >
                  <input
                    type="checkbox"
                    checked={isShown}
                    disabled={isSaving}
                    onChange={() => toggle(href, !isShown)}
                    className="size-4 shrink-0 cursor-pointer accent-slate-900"
                  />
                  <Icon className="size-4 shrink-0 text-slate-500" aria-hidden />
                  <span>{name}</span>
                </label>
              );
            })}
          </div>
        ))}
      </div>
    </fieldset>
  );
}
