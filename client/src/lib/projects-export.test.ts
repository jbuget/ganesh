import { describe, expect, it } from "vitest";

import { EXPORT_HEADERS, projectsSheet, workbookName } from "./projects-export";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const cost = (over: Partial<ProjectListItemResponse["cost"]> = {}) => ({
  build_days: 0,
  run_days: 0,
  estimated_days: null,
  monthly_run_rate: null,
  has_overrun: false,
  ...over,
});

const mission = (
  over: Partial<ProjectListItemResponse["project"]> & { label: string },
  rest: Partial<ProjectListItemResponse> = {},
): ProjectListItemResponse =>
  ({
    project: {
      id: 1,
      kind: "project",
      status: null,
      parent_id: null,
      is_active: true,
      archived_at: null,
      estimated_days: null,
      category: null,
      priority: null,
      ...over,
    },
    leads: [],
    contributors: [],
    links: [],
    delivered_days: 0,
    cost: cost(),
    tree_cost: cost(),
    comments: 0,
    latest_update: null,
    ...rest,
  }) as unknown as ProjectListItemResponse;

type Sheet = ReturnType<typeof projectsSheet>;

/** What each column says on a mission's row, found by its name. */
function rowOf(sheet: Sheet, label: string) {
  const row = sheet.find((cells) => cells[0]?.value === label);
  if (!row) throw new Error(`Aucune ligne pour « ${label} »`);
  return Object.fromEntries(
    EXPORT_HEADERS.map((header, index) => [header, row[index]?.value ?? null]),
  );
}

/** The first cell of each row, header aside: the missions, in order. */
function labels(sheet: Sheet) {
  return sheet.slice(1).map((cells) => cells[0]?.value);
}

describe("projectsSheet", () => {
  it("opens on a header row naming every column", () => {
    const sheet = projectsSheet([]);

    expect(sheet[0].map((cell) => cell?.value)).toEqual([...EXPORT_HEADERS]);
  });

  it("reads each mission column by column, as the screen shows it", () => {
    const sheet = projectsSheet([
      mission(
        {
          label: "Portail",
          status: "development",
          priority: "high",
          category: "structure_platform",
        },
        {
          cost: cost({ build_days: 12.5, run_days: 3, estimated_days: 20 }),
          comments: 4,
          leads: [{ display_name: "Ada" }, { display_name: "Alan" }],
          contributors: [{ display_name: "Grace" }],
        } as Partial<ProjectListItemResponse>,
      ),
    ]);

    expect(rowOf(sheet, "Portail")).toMatchObject({
      Projet: "Portail",
      Type: "Projet",
      Phase: "Réalisation",
      Priorité: "Haute",
      Catégorie: "Structurer la plateforme",
      "Build (j)": 12.5,
      "Estimé (j)": 20,
      "Run (j)": 3,
      Référents: "Ada, Alan",
      Intervenants: "Grace",
      Échanges: 4,
    });
  });

  it("lays each work package under its project, naming its parent", () => {
    const sheet = projectsSheet([
      mission({ id: 1, label: "Portail" }),
      mission({ id: 2, label: "Lot API", kind: "work_package", parent_id: 1 }),
      mission({ id: 3, label: "Zeta" }),
    ]);

    expect(labels(sheet)).toEqual(["Portail", "Lot API", "Zeta"]);
    expect(rowOf(sheet, "Lot API")).toMatchObject({
      Type: "Sous-projet",
      "Rattaché à": "Portail",
    });
  });

  it("brings up off-project activities at the end", () => {
    const sheet = projectsSheet([
      mission({ id: 1, label: "Congés", kind: "off_project" }),
      mission({ id: 2, label: "Portail" }),
    ]);

    expect(labels(sheet)).toEqual(["Portail", "Congés"]);
    expect(rowOf(sheet, "Congés")).toMatchObject({ Type: "Hors projet" });
  });

  it("tells an archived mission from a live one", () => {
    const sheet = projectsSheet([
      mission({ id: 1, label: "Portail" }),
      mission({ id: 2, label: "Ancien", is_active: false }),
    ]);

    expect(rowOf(sheet, "Portail")).toMatchObject({ Statut: "Active" });
    expect(rowOf(sheet, "Ancien")).toMatchObject({ Statut: "Archivée" });
  });

  it("leaves what is not filled in empty rather than writing a zero", () => {
    const sheet = projectsSheet([mission({ label: "Portail" })]);

    expect(rowOf(sheet, "Portail")).toMatchObject({
      Phase: null,
      Priorité: null,
      Catégorie: null,
      "Estimé (j)": null,
      "Run (j/mois)": null,
      Référents: null,
      Liens: null,
      "Dernier échange": null,
    });
  });

  it("carries the days as numbers, so the spreadsheet can total them", () => {
    const sheet = projectsSheet([
      mission({ label: "Portail" }, { cost: cost({ build_days: 12.5 }) }),
    ]);

    const row = sheet[1];
    expect(row[EXPORT_HEADERS.indexOf("Build (j)")]).toMatchObject({
      type: Number,
      value: 12.5,
    });
  });

  it("counts a project's own cost, its sub-projects being rows of their own", () => {
    const sheet = projectsSheet([
      mission(
        { id: 1, label: "Portail" },
        { cost: cost({ build_days: 8 }), tree_cost: cost({ build_days: 20 }) },
      ),
      mission(
        { id: 2, label: "Lot API", kind: "work_package", parent_id: 1 },
        { cost: cost({ build_days: 12 }), tree_cost: cost({ build_days: 12 }) },
      ),
    ]);

    expect(rowOf(sheet, "Portail")).toMatchObject({ "Build (j)": 8 });
    expect(rowOf(sheet, "Lot API")).toMatchObject({ "Build (j)": 12 });
  });

  it("spells out the links the row shows as icons", () => {
    const sheet = projectsSheet([
      mission({ label: "Portail" }, {
        links: [
          { id: 1, label: "Dépôt", url: "https://git/portail", icon: "repository" },
          { id: 2, label: "Maquette", url: "https://figma/portail", icon: "design" },
        ],
      } as Partial<ProjectListItemResponse>),
    ]);

    expect(rowOf(sheet, "Portail")).toMatchObject({
      Liens: "Dépôt : https://git/portail\nMaquette : https://figma/portail",
    });
  });

  it("dates the latest message and names who wrote it", () => {
    const sheet = projectsSheet([
      mission({ label: "Portail" }, {
        comments: 2,
        latest_update: {
          body: "Mise en recette",
          published_at: "2026-09-18T10:00:00Z",
          author: { display_name: "Ada" },
        },
      } as Partial<ProjectListItemResponse>),
    ]);

    expect(rowOf(sheet, "Portail")).toMatchObject({
      "Dernier échange": "18/09/2026",
      "Auteur du dernier échange": "Ada",
    });
  });
});

describe("workbookName", () => {
  it("dates the file, so two exports do not overwrite each other", () => {
    expect(workbookName(new Date(2026, 8, 19))).toBe("projets-2026-09-19.xlsx");
  });
});

/**
 * The sheet goes through the writer for real.
 *
 * Nothing else catches a cell the library refuses — a wrong type, a value
 * where it expects none: the screen would open, the button would click, and
 * only the download would fail.
 */
describe("the workbook the writer produces", () => {
  it("comes out a valid xlsx archive", async () => {
    const { default: writeXlsxFile } = await import("write-excel-file/node");
    const sheet = projectsSheet([
      mission(
        {
          id: 1,
          label: "Portail",
          status: "development",
          priority: "high",
          category: "structure_platform",
        },
        {
          cost: cost({ build_days: 12.5, run_days: 3, estimated_days: 20 }),
          leads: [{ display_name: "Ada" }],
          links: [
            { id: 1, label: "Dépôt", url: "https://git/portail", icon: "repository" },
          ],
          comments: 2,
          latest_update: {
            body: "Mise en recette",
            published_at: "2026-09-18T10:00:00Z",
            author: { display_name: "Ada" },
          },
        } as Partial<ProjectListItemResponse>,
      ),
      mission(
        {
          id: 2,
          label: "Lot API",
          kind: "work_package",
          parent_id: 1,
          is_active: false,
        },
        { cost: cost({ has_overrun: true }) },
      ),
      mission({ id: 3, label: "Congés", kind: "off_project" }),
    ]);

    const buffer = await writeXlsxFile(sheet, { sheet: "Projets" }).toBuffer();

    expect(buffer.subarray(0, 2).toString()).toBe("PK");
  });
});
