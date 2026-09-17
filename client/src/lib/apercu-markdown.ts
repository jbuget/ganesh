/** Une infobulle ne rend pas le markdown : elle en donne le texte. */
const LONGUEUR_MAX = 240;

/**
 * Le texte d'une mise a jour, debarrasse de sa syntaxe et resserre.
 *
 * Le fil s'ecrit en markdown, et une infobulle n'a pas de quoi le rendre : on
 * y montre ce que le message dit, pas comment il est ecrit. Les marques sont
 * donc otees plutot qu'affichees telles quelles — `**recette**` se lirait mal
 * dans un apercu.
 *
 * Les puces font exception : leur tiret devient un point median, parce qu'une
 * liste privee de ses marques se lirait comme une phrase hachee.
 */
export function apercuMarkdown(markdown: string): string {
  const texte = markdown
    .replace(/```[\s\S]*?```/g, "…")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/^\s{0,3}>\s?/gm, "")
    .replace(/^\s{0,3}[-*+]\s+/gm, "• ")
    .replace(/^\s{0,3}\d+\.\s+/gm, "• ")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    // L'underscore ne marque l'emphase qu'en bordure de mot : au milieu, il
    // appartient au mot. `latest_by_project` n'est pas de l'italique.
    .replace(/(?<![\w_])__(.+?)__(?![\w_])/g, "$1")
    .replace(/(?<![\w_])_(.+?)_(?![\w_])/g, "$1")
    .replace(/~~(.*?)~~/g, "$1")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{2,}/g, "\n")
    .trim();

  if (texte.length <= LONGUEUR_MAX) return texte;

  // Couper au dernier espace : un mot tranche se lit comme une coquille.
  const coupe = texte.slice(0, LONGUEUR_MAX);
  const espace = coupe.lastIndexOf(" ");
  return `${(espace > 0 ? coupe.slice(0, espace) : coupe).trimEnd()}…`;
}
