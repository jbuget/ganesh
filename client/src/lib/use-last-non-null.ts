"use client";

import { useState } from "react";

/**
 * Conserve la derniere valeur non nulle recue.
 *
 * Un dialogue se ferme avec une animation : si l'etat qui le nourrit repasse a
 * `null` au moment du declenchement, son contenu se vide sous les yeux de
 * l'utilisateur pendant la sortie. On garde donc de quoi l'afficher jusqu'au
 * bout.
 *
 * L'ajustement se fait pendant le rendu, comme React le recommande pour une
 * valeur derivee d'une prop : ni effet, ni mutation de ref.
 */
export function useLastNonNull<T>(value: T | null): T | null {
  const [dernier, setDernier] = useState<T | null>(value);

  if (value !== null && value !== dernier) {
    setDernier(value);
    return value;
  }

  return value ?? dernier;
}
