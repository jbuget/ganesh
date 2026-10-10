"use client";

import { Flag } from "lucide-react";

interface FollowMarkProps {
  /** Whether the team keeps an eye on the mission right now. */
  followed: boolean;
  /**
   * Raises or lowers the mark, in one click.
   *
   * Absent where the mark is only read: it then shows on a followed mission
   * and nothing at all on the others — unless it is labelled.
   */
  onToggle?: () => void;
  /**
   * Writes the state beside the flag. A sheet reads it as a value, where a
   * row or a card only needs the flag.
   */
  labelled?: boolean;
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
export function FollowMark({
  followed,
  onToggle,
  labelled = false,
  className = "",
}: FollowMarkProps) {
  const state = followed ? "Projet suivi" : "Non suivi";
  const flag = (
    <Flag
      className={`size-3.5 shrink-0 ${followed ? "fill-current" : ""}`}
      aria-hidden
    />
  );
  const words = labelled && (
    <span className={followed ? "text-slate-800" : "text-slate-500"}>{state}</span>
  );

  if (!onToggle) {
    if (!followed && !labelled) return null;
    return (
      <span
        aria-label={labelled ? undefined : state}
        title={state}
        className={`inline-flex items-center gap-1.5 rounded py-0.5 text-sm ${
          followed ? "text-amber-600" : "text-slate-300"
        } ${labelled ? "" : "px-1"} ${className}`}
      >
        {flag}
        {words}
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
      className={`inline-flex cursor-pointer items-center gap-1.5 rounded px-1 py-0.5 text-sm transition-colors hover:bg-amber-50 ${
        followed
          ? "text-amber-600 hover:text-amber-800"
          : "text-slate-300 hover:text-amber-700"
      } ${className}`}
    >
      {flag}
      {words}
    </button>
  );
}
