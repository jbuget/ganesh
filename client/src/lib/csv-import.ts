import type { ImportLineRequest } from "@/lib/api/generated/model";

/**
 * Column headers understood in an imported file, with their aliases.
 *
 * A spreadsheet is written by people, not by the code: the French headers the
 * team has been using keep working alongside the English field names, so an
 * export prepared last month still imports today.
 */
export const COLUMNS = {
  label: ["label", "libelle"],
  kind: ["kind", "type"],
  parent_label: ["parent_label", "parent"],
  status: ["status", "statut"],
  estimated_days: ["estimated_days", "estime_j"],
  monday_item_id: ["monday_item_id"],
} as const;

const SEPARATORS = [";", ",", "\t"];

/**
 * Cell values people still write in French, and what they mean.
 *
 * The same reasoning as the headers: a spreadsheet filled in last month must
 * keep importing. An unknown value is passed through untouched, and the server
 * rejects it with its own message.
 */
const FRENCH_KINDS: Record<string, string> = {
  projet: "project",
  lot: "work_package",
  hors_projet: "off_project",
};

const FRENCH_STATUSES: Record<string, string> = {
  cadrage: "scoping",
  realisation: "development",
  deploiement: "deployment",
  exploitation: "operations",
};

/** Guesses the separator: a French export often comes out semicolon-separated. */
function detectSeparator(entete: string): string {
  return (
    SEPARATORS.map((s) => ({ s, n: entete.split(s).length }))
      .sort((a, b) => b.n - a.n)
      .find((c) => c.n > 1)?.s ?? ";"
  );
}

function split(line: string, separator: string): string[] {
  return line.split(separator).map((c) => c.trim().replace(/^"|"$/g, ""));
}

/**
 * Turns a CSV into import lines.
 *
 * The first line names the columns: their order does not matter, and those not
 * recognised are ignored rather than failing the whole file — a Monday export
 * carries plenty of other columns.
 */
export function parseProjectsCsv(content: string): ImportLineRequest[] {
  const lines = content
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length < 2) return [];

  const separator = detectSeparator(lines[0]);
  const headers = split(lines[0], separator).map((e) => e.toLowerCase());

  return lines.slice(1).map((line) => {
    const cells = split(line, separator);
    const value = (column: keyof typeof COLUMNS) => {
      const index = COLUMNS[column]
        .map((alias) => headers.indexOf(alias))
        .find((position) => position !== -1);
      return index === undefined ? "" : (cells[index] ?? "");
    };

    const estimated = Number.parseFloat(value("estimated_days").replace(",", "."));

    return {
      label: value("label"),
      kind: (FRENCH_KINDS[value("kind")] ||
        value("kind") ||
        "project") as ImportLineRequest["kind"],
      parent_label: value("parent_label") || null,
      status: (FRENCH_STATUSES[value("status")] ||
        value("status") ||
        "exploration") as ImportLineRequest["status"],
      estimated_days: Number.isFinite(estimated) ? estimated : null,
      monday_item_id: value("monday_item_id") || null,
    };
  });
}
