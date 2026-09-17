"use client";

interface StatusBadgeProps {
  is_active: boolean;
  /** Seul un manager coupe ou retablit un acces, et jamais le sien. */
  modifiable: boolean;
  onToggle: (is_active: boolean) => void | Promise<void>;
}

/**
 * Acces d'un utilisateur : ouvert, ou coupe.
 *
 * Les deux etats se nomment. Ne signaler que l'ecart laissait une case vide
 * dont on ne savait pas si elle voulait dire « actif » ou « pas encore charge ».
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
