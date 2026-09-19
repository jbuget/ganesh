import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { category, phaseLabel, priority } from "@/lib/board";
import { formatShortDate } from "@/lib/dates";
import { buildProjectTree } from "@/lib/project-tree";

/**
 * The columns of the exported workbook, in reading order.
 *
 * They follow the reference list — where the mission stands, what it weighs,
 * who looks after it — and add what the screen says by other means than a
 * column: the kind and the parent, which the indentation shows; the estimate
 * and the run pace, which the Build and Run cells carry inside their text;
 * whether the mission is archived, which only the filter tells.
 */
export const EXPORT_HEADERS = [
  "Projet",
  "Type",
  "Rattaché à",
  "Statut",
  "Phase",
  "Priorité",
  "Catégorie",
  "Build (j)",
  "Estimé (j)",
  "Dépassement",
  "Run (j)",
  "Run (j/mois)",
  "Référents",
  "Intervenants",
  "Liens",
  "Échanges",
  "Dernier échange",
  "Auteur du dernier échange",
] as const;

/** A filled cell, as `write-excel-file` reads one. An empty one is `null`. */
interface ExportCell {
  value: string | number | boolean;
  type: StringConstructor | NumberConstructor | BooleanConstructor;
  fontWeight?: "bold";
  wrap?: boolean;
  alignVertical?: "top";
}

type SheetRow = (ExportCell | null)[];

const KINDS: Record<string, string> = {
  project: "Projet",
  work_package: "Sous-projet",
  off_project: "Hors projet",
};

const text = (value: string | null): ExportCell | null =>
  value ? { value, type: String } : null;

/**
 * A number of days, or nothing.
 *
 * Zero is not a figure to read here any more than in the list: a mission
 * nobody has declared on stays empty, and an empty cell does not drag a column
 * average down.
 */
const days = (value: number | null | undefined): ExportCell | null =>
  value ? { value: Number(value.toFixed(2)), type: Number } : null;

const count = (value: number): ExportCell | null =>
  value ? { value, type: Number } : null;

/**
 * The addresses attached to a mission, one per line inside the cell.
 *
 * The row shows them as icons, which a file cannot carry: the label and the
 * address are written out, since a link one cannot click is a link one must be
 * able to copy.
 */
function links(attached: { label: string; url: string }[]): ExportCell | null {
  const cell = text(attached.map((link) => `${link.label} : ${link.url}`).join("\n"));
  // Without the wrap, Excel keeps the line breaks in the value but shows the
  // whole thing on one line: the addresses would run into each other.
  return cell && { ...cell, wrap: true, alignVertical: "top" };
}

/** The people who look after a mission, in one cell. */
function names(members: { display_name: string }[]): ExportCell | null {
  return text(members.map((member) => member.display_name).join(", "));
}

function row(mission: ProjectListItemResponse, parentLabel: string | null): SheetRow {
  const { project } = mission;
  // Each row carries what the mission itself cost, not what its sub-projects
  // add up to: they are rows of their own here, and the tree total would count
  // them twice as soon as the reader sums a column.
  const { cost } = mission;
  const latest = mission.latest_update;

  return [
    text(project.label),
    text(KINDS[project.kind] ?? project.kind),
    text(parentLabel),
    text(project.is_active ? "Active" : "Archivée"),
    text(project.status ? phaseLabel(project.status) : null),
    text(priority(project.priority)?.label ?? null),
    text(category(project.category)?.label ?? null),
    days(cost.build_days),
    days(cost.estimated_days),
    cost.has_overrun ? { value: true, type: Boolean } : null,
    days(cost.run_days),
    days(cost.monthly_run_rate),
    names(mission.leads),
    names(mission.contributors),
    links(mission.links),
    count(mission.comments),
    text(latest ? formatShortDate(latest.published_at) : null),
    text(latest?.author.display_name ?? null),
  ];
}

/**
 * The reference list as a sheet: one header row, then one row per mission.
 *
 * The order is the screen's own — each project followed by its sub-projects,
 * off-project work at the end — so that whoever exports finds the workbook
 * arranged the way they left the list.
 */
export function projectsSheet(missions: ProjectListItemResponse[]): SheetRow[] {
  const header: SheetRow = EXPORT_HEADERS.map((label) => ({
    value: label,
    type: String,
    fontWeight: "bold",
  }));

  const rows = buildProjectTree(missions).flatMap(({ mission, workPackages }) => [
    row(mission, null),
    ...workPackages.map((workPackage) => row(workPackage, mission.project.label)),
  ]);

  // Off-project work left the screen, but not the reference list: an export
  // meant to be worked on elsewhere must not lose the missions the days are
  // also declared on. It comes last, having neither phase nor estimate.
  const activities = missions
    .filter((mission) => mission.project.kind === "off_project")
    .sort((a, b) => a.project.label.localeCompare(b.project.label, "fr"))
    .map((activity) => row(activity, null));

  return [header, ...rows, ...activities];
}

/** How wide each column opens, in characters. */
const COLUMN_WIDTHS = [
  38, 12, 28, 10, 14, 10, 24, 10, 10, 13, 10, 13, 26, 30, 44, 10, 16, 24,
];

/** `projets-2026-09-19.xlsx`: dated, so two exports do not overwrite each other. */
export function workbookName(today: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  const stamp = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  return `projets-${stamp}.xlsx`;
}

/**
 * Writes the workbook and hands it to the browser.
 *
 * The writer is loaded on demand: it weighs more than the screen it serves,
 * and nobody should pay for it before asking for an export.
 */
export async function downloadProjectsWorkbook(
  missions: ProjectListItemResponse[],
  today: Date,
): Promise<void> {
  const { default: writeXlsxFile } = await import("write-excel-file/browser");

  await writeXlsxFile(projectsSheet(missions), {
    sheet: "Projets",
    // The header stays in view: sixty rows down, one no longer knows which
    // column one is reading — the same reason the list pins its own.
    stickyRowsCount: 1,
    columns: COLUMN_WIDTHS.map((width) => ({ width })),
  }).toFile(workbookName(today));
}
