/**
 * L'accord en nombre, écrit une fois.
 *
 * Le type checker ne voit pas un libellé composé à l'exécution, et les tests
 * portent sur le compte plutôt que sur la formule : un « 2 projet » ne se
 * rattrape qu'en ouvrant l'écran. Autant n'avoir qu'un seul endroit où il
 * puisse être faux.
 *
 * Le français accorde à partir de deux : « 0 projet », « 1 projet »,
 * « 2 projets ».
 */

/** « 3 projets », « 1 projet ». */
export function plural(count: number, word: string): string {
  return count > 1 ? `${word}s` : word;
}

/** L'accord seul, pour ce que le mot ne porte pas : « 2 livrés ». */
export function s(count: number): string {
  return count > 1 ? "s" : "";
}
