"use client";

import { Flag } from "lucide-react";

interface FollowMarkProps {
  /** Whether the team keeps an eye on the mission right now. */
  followed: boolean;
  /**
   * Raises or lowers the mark, in one click.
   *
   * Absent for a reader who may not write: the mark then shows on a followed
   * mission and nothing at all on the others.
   */
  onToggle?: () => void;
  className?: string;
}

/**
 * Ce que l'équipe suit de près en ce moment : à faire, en cours, livré il y a
 * peu, ou qui vient de faire parler de lui.
 *
 * Posé et levé d'un clic, à la main : le projet le porte lui-même, et un lot
 * le porte pour lui seul. Il sert de filtre — « Suivis » dans la liste comme
 * sur le tableau.
 */
export function FollowMark({ followed, onToggle, className = "" }: FollowMarkProps) {
  if (!onToggle) {
    if (!followed) return null;
    return (
      <span
        aria-label="Projet suivi"
        title="Projet suivi"
        className={`inline-flex items-center rounded px-1 py-0.5 text-amber-600 ${className}`}
      >
        <Flag className="size-3.5 shrink-0 fill-current" aria-hidden />
      </span>
    );
  }

  const gesture = followed ? "Ne plus suivre ce projet" : "Suivre ce projet";
  return (
    <button
      type="button"
      aria-label={gesture}
      aria-pressed={followed}
      title={gesture}
      // La ligne entière ouvre déjà le projet : sans cela, le clic l'ouvrirait
      // en plus de poser la marque.
      onClick={(event) => {
        event.stopPropagation();
        onToggle();
      }}
      className={`inline-flex cursor-pointer items-center rounded px-1 py-0.5 transition-colors hover:bg-amber-50 ${
        followed
          ? "text-amber-600 hover:text-amber-800"
          : "text-slate-300 hover:text-amber-700"
      } ${className}`}
    >
      <Flag
        className={`size-3.5 shrink-0 ${followed ? "fill-current" : ""}`}
        aria-hidden
      />
    </button>
  );
}
