"use client";

import type { ApiKeyScope } from "@/lib/api/generated/model";
import { SCOPES, coveredBy, scopeLabel } from "@/lib/api-keys";

interface ScopePickerProps {
  value: ApiKeyScope[];
  onChange: (scopes: ApiKeyScope[]) => void;
  /** Read-only where the reader may not change what a key opens. */
  disabled?: boolean;
}

/**
 * What a key opens, ticked one scope at a time.
 *
 * A broad scope ticks and **locks** what it carries, naming where each locked
 * box gets its right from: the reach of « Tous » is seen where it is decided
 * rather than discovered later in a log. The two broad ones are independent,
 * one per verb — neither locks the other, so ticking both stays possible and
 * each stays untickable back.
 *
 * Shared by the creation dialog and the panel: what a key opens must read the
 * same whether one is minting it or correcting it.
 */
export function ScopePicker({ value, onChange, disabled = false }: ScopePickerProps) {
  function toggle(scope: ApiKeyScope) {
    onChange(
      value.includes(scope)
        ? value.filter((kept) => kept !== scope)
        : [...value, scope],
    );
  }

  return (
    <div className="space-y-1.5">
      {SCOPES.map((scope) => {
        const covering = coveredBy(scope.value, value);
        const locked = disabled || covering !== null;
        return (
          <label
            key={scope.value}
            className={[
              "flex items-start gap-2 text-sm",
              locked ? "cursor-default" : "cursor-pointer",
            ].join(" ")}
          >
            <input
              type="checkbox"
              checked={covering !== null || value.includes(scope.value)}
              disabled={locked}
              onChange={() => toggle(scope.value)}
              className="mt-0.5 size-4 rounded border-slate-300 enabled:cursor-pointer disabled:cursor-default"
            />
            <span className={covering ? "opacity-50" : undefined}>
              <span className="text-slate-800">{scope.label}</span>
              <span className="block text-xs text-slate-500">
                {covering ? `Inclus dans « ${scopeLabel(covering)} »` : scope.hint}
              </span>
            </span>
          </label>
        );
      })}
    </div>
  );
}
