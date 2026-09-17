import type { ImportLineRequest } from "@/lib/api/generated/model";

/** Colonnes reconnues, dans l'ordre attendu du fichier. */
export const COLONNES = [
  "label",
  "kind",
  "parent_label",
  "statut",
  "estime_j",
  "monday_item_id",
] as const;

const SEPARATEURS = [";", ",", "\t"];

/** Devine le separateur : un export francais sort souvent en point-virgule. */
function detecterSeparateur(entete: string): string {
  return (
    SEPARATEURS.map((s) => ({ s, n: entete.split(s).length }))
      .sort((a, b) => b.n - a.n)
      .find((c) => c.n > 1)?.s ?? ";"
  );
}

function decouper(ligne: string, separateur: string): string[] {
  return ligne.split(separateur).map((c) => c.trim().replace(/^"|"$/g, ""));
}

/**
 * Convertit un CSV en lignes d'import.
 *
 * La premiere ligne nomme les colonnes : leur ordre n'a pas d'importance, et
 * celles qu'on ne reconnait pas sont ignorees plutot que de faire echouer le
 * fichier entier — un export Monday porte bien d'autres colonnes.
 */
export function parseProjectsCsv(contenu: string): ImportLineRequest[] {
  const lignes = contenu
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lignes.length < 2) return [];

  const separateur = detecterSeparateur(lignes[0]);
  const entetes = decouper(lignes[0], separateur).map((e) => e.toLowerCase());

  return lignes.slice(1).map((ligne) => {
    const cellules = decouper(ligne, separateur);
    const valeur = (colonne: string) => {
      const index = entetes.indexOf(colonne);
      return index === -1 ? "" : (cellules[index] ?? "");
    };

    const estime = Number.parseFloat(valeur("estime_j").replace(",", "."));

    return {
      label: valeur("label"),
      kind: (valeur("kind") || "projet") as ImportLineRequest["kind"],
      parent_label: valeur("parent_label") || null,
      statut: (valeur("statut") || "exploration") as ImportLineRequest["statut"],
      estime_j: Number.isFinite(estime) ? estime : null,
      monday_item_id: valeur("monday_item_id") || null,
    };
  });
}
