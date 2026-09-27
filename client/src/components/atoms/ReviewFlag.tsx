"use client";

import { Flag } from "lucide-react";

interface ReviewFlagProps {
  /** How many of the mission's updates are waiting to be discussed. */
  count: number;
  /**
   * Leads to the thread, where the mark was left and where the reason is.
   *
   * Absent, the mark shows without being clickable: on a card the whole card
   * already opens the mission.
   */
  onOpen?: () => void;
}

/**
 * Ce qui attend d'être discuté sur une mission, en une marque.
 *
 * Dérivée du fil, jamais portée par la mission : ce qui se voit ici s'éteint
 * quand la revue a lu, sans que personne ait à décocher quoi que ce soit.
 *
 * Une mission dont rien n'attend n'affiche rien — dans une liste, on ne
 * montre que ce qui se lit. Le nombre ne s'écrit qu'à partir de deux : à un,
 * le drapeau le dit déjà.
 */
export function ReviewFlag({ count, onOpen }: ReviewFlagProps) {
  if (count === 0) return null;

  const what =
    count > 1 ? `${count} mises à jour à discuter` : "Une mise à jour à discuter";
  const marking = (
    <>
      {count > 1 && count}
      <Flag className="size-3.5 shrink-0" aria-hidden />
    </>
  );

  if (!onOpen) {
    return (
      <span
        aria-label={what}
        title={what}
        className="inline-flex items-center gap-1 rounded px-1 py-0.5 text-xs font-medium tabular-nums text-amber-700"
      >
        {marking}
      </span>
    );
  }

  return (
    <button
      type="button"
      aria-label={what}
      title={what}
      // La ligne entière ouvre déjà la mission : sans cela, le clic
      // l'ouvrirait deux fois, la seconde sur le mauvais onglet.
      onClick={(event) => {
        event.stopPropagation();
        onOpen();
      }}
      className="inline-flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 text-xs font-medium tabular-nums text-amber-700 transition-colors hover:bg-amber-50 hover:text-amber-900"
    >
      {marking}
    </button>
  );
}
