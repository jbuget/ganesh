"use client";

interface StatusBadgeProps {
  actif: boolean;
  /** Seul un manager coupe ou retablit un acces, et jamais le sien. */
  modifiable: boolean;
  onToggle: (actif: boolean) => void | Promise<void>;
}

/**
 * Acces d'un utilisateur : ouvert, ou coupe.
 *
 * Les deux etats se nomment. Ne signaler que l'ecart laissait une case vide
 * dont on ne savait pas si elle voulait dire « actif » ou « pas encore charge ».
 */
export function StatusBadge({ actif, modifiable, onToggle }: StatusBadgeProps) {
  const pastille = actif
    ? "bg-emerald-50 text-emerald-700"
    : "bg-slate-100 text-slate-500";
  const libelle = actif ? "Actif" : "Désactivé";

  if (!modifiable) {
    return (
      <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${pastille}`}>
        {libelle}
      </span>
    );
  }

  return (
    <button
      type="button"
      aria-label={actif ? "Désactiver ce compte" : "Réactiver ce compte"}
      onClick={() => void onToggle(!actif)}
      className={`cursor-pointer rounded px-1.5 py-0.5 text-xs font-medium transition-colors hover:ring-1 hover:ring-slate-300 ${pastille}`}
    >
      {libelle}
    </button>
  );
}
