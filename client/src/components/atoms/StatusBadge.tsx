"use client";

interface StatusBadgeProps {
  is_active: boolean;
  /** Only a manager cuts off or restores access, and never their own. */
  modifiable: boolean;
  onToggle: (is_active: boolean) => void | Promise<void>;
}

/**
 * A user's access: open, or cut off.
 *
 * Both states are named. Flagging only the exception left an empty cell one
 * could not tell meant \u00ab active \u00bb or \u00ab not loaded yet \u00bb.
 */
export function StatusBadge({ is_active, modifiable, onToggle }: StatusBadgeProps) {
  const dot = is_active
    ? "bg-emerald-50 text-emerald-700"
    : "bg-slate-100 text-slate-500";
  const label = is_active ? "Actif" : "Désactivé";

  if (!modifiable) {
    return (
      <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${dot}`}>
        {label}
      </span>
    );
  }

  return (
    <button
      type="button"
      aria-label={is_active ? "Désactiver ce compte" : "Réactiver ce compte"}
      onClick={() => void onToggle(!is_active)}
      className={`cursor-pointer rounded px-1.5 py-0.5 text-xs font-medium transition-colors hover:ring-1 hover:ring-slate-300 ${dot}`}
    >
      {label}
    </button>
  );
}
