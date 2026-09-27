import {
  CalendarDays,
  ChartNoAxesColumn,
  Cog,
  Flag,
  FolderKanban,
  GanttChartSquare,
  Home,
  Inbox,
  KanbanSquare,
  KeyRound,
  Milestone,
  Newspaper,
  ScrollText,
  Smile,
  TableProperties,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { Role } from "@/lib/api/generated/model";
import { holds } from "@/lib/roles";

/**
 * The band of the bar a screen is listed under.
 *
 * The bar used to be one flat list of sixteen tabs, where « Saisie des temps »
 * and « API / MCP » read at the same weight. The bands say the shape instead:
 * what I do, what the team works on, what is read of it, who we are, and what
 * holds the whole thing up.
 *
 * `"aside"` is the one that is not a band: the screen exists, the palette
 * leads to it, the bar does not list it. It is for what is reached from where
 * it is read — La Gazette, from the band above « Quoi de neuf » on the home
 * screen — and it is a decision each time, never a place to put what did not
 * fit.
 */
export type Band = "work" | "portfolio" | "steering" | "team" | "platform" | "aside";

/**
 * What each band is called above its tabs.
 *
 * The first carries none: what one does every morning needs no heading, and a
 * title above the very first tab would push « Accueil » down for nothing.
 */
const BAND_LABELS: Record<Exclude<Band, "aside">, string | null> = {
  work: null,
  portfolio: "Portefeuille",
  steering: "Pilotage",
  team: "Équipe",
  platform: "Plateforme",
};

export interface Screen {
  href: string;
  label: string;
  Icon: LucideIcon;
  band: Band;
  /**
   * The rung one has to stand on to see it at all.
   *
   * Almost nothing carries this: the navigation says what exists and the
   * permission lives on the actions — « Utilisateurs » and « API / MCP »
   * are shown to everyone and refuse the gestures. « Administration » is the
   * exception, and it is one because it has no read a manager may have: the
   * whole screen is the permission.
   */
  seenFrom?: Role;
}

/**
 * The screens the application is made of, in the order they are read in.
 *
 * Written once: the sidebar bands them, the palette leads to them, and two
 * lists of the same screens would end up disagreeing about what exists. Which
 * is why a screen taken out of the bar stays here, banded `"aside"`: it is
 * still searchable, still reachable, and still counted by the test that says
 * the list is whole.
 */
export const SCREENS: readonly Screen[] = [
  // « Accueil » opens the list and holds the root: it is what one lands on
  // after signing in, and it names what to do before the screens that do it.
  { href: "/", label: "Accueil", Icon: Home, band: "work" },
  { href: "/timesheet", label: "Saisie des temps", Icon: CalendarDays, band: "work" },

  { href: "/kanban", label: "Kanban", Icon: KanbanSquare, band: "portfolio" },
  // Beside the board rather than beside the projects: it is read when the
  // revue opens, on the screen the revue is held on.
  { href: "/agenda", label: "À discuter", Icon: Flag, band: "portfolio" },
  { href: "/projects", label: "Projets", Icon: FolderKanban, band: "portfolio" },
  // Between the projects and what is read of them: a need is what a mission
  // is born of, and it is kept out of the reference list until it is. A tab of
  // « Projets » would say the two are one thing seen twice, which is the whole
  // confusion the recueil exists to prevent — and a guest, who reaches this
  // and nothing else, would be sent through a screen they cannot open.
  { href: "/requests", label: "Demandes", Icon: Inbox, band: "portfolio" },

  {
    href: "/activity-summary",
    label: "Synthèse d'activité",
    Icon: TableProperties,
    band: "steering",
  },
  { href: "/planning", label: "Planification", Icon: GanttChartSquare, band: "steering" },
  { href: "/roadmap", label: "Feuille de route", Icon: Milestone, band: "steering" },

  // Off the bar, and read from the home screen instead: it tells the month of
  // the whole company where « Quoi de neuf » tells the news of my own
  // projects, and one above the other reads as a single movement, from the
  // company down to me. A monthly page listed every day beside the screens one
  // opens hourly asked for a rank it never earned.
  { href: "/gazette", label: "La Gazette", Icon: Newspaper, band: "aside" },

  // The mirror before the list: the band opens on how the team is, and then
  // says who it is made of. A screen of its own rather than a tab of the one
  // below — it reads and never writes, where « Utilisateurs » is where a role
  // is given away, and an entry in the bar has to lead to a screen rather than
  // to somebody else's tab.
  { href: "/mood", label: "Moral", Icon: Smile, band: "team" },
  // Shown to everyone, as « API / MCP » is: the navigation says what exists,
  // and the permission lives on the actions.
  { href: "/users", label: "Utilisateurs", Icon: Users, band: "team" },

  // The register read across, where a mission's « Journal » tab reads one
  // mission's. Same word for the same thing, and the only screen a deleted
  // project can still be found from: its lines outlive it, with no mission
  // left to open them in.
  { href: "/logs", label: "Journal", Icon: ScrollText, band: "platform" },
  // « Statistiques » reads the other screens rather than standing beside
  // them — how much of the month is covered, and which surfaces nobody opens.
  // That is a read of the application, which is what this band holds.
  { href: "/stats", label: "Statistiques", Icon: ChartNoAxesColumn, band: "platform" },
  { href: "/api-mcp", label: "API / MCP", Icon: KeyRound, band: "platform" },
  // Last, and only an administrator sees it at all: it is about the platform
  // itself rather than about what the platform holds.
  {
    href: "/admin",
    label: "Administration",
    Icon: Cog,
    band: "platform",
    seenFrom: "ADMIN",
  },
] as const;

/** The screens a given role is shown. */
export function screensFor(role: Role | undefined): readonly Screen[] {
  return SCREENS.filter((screen) => !screen.seenFrom || holds(role, screen.seenFrom));
}

/** One band of the bar: its heading, if it has one, and the tabs under it. */
export interface NavBand {
  band: Exclude<Band, "aside">;
  label: string | null;
  screens: readonly Screen[];
}

/**
 * The bar a given role reads, banded.
 *
 * Built from `SCREENS` in its own order rather than from a second list, so a
 * screen can never be in one and missing from the other. A band whose every
 * screen is out of reach — « Plateforme » would be, were « Administration »
 * alone in it — is not drawn: a heading over nothing is worse than no heading.
 */
export function bandsFor(role: Role | undefined): readonly NavBand[] {
  const bands: NavBand[] = [];

  for (const screen of screensFor(role)) {
    if (screen.band === "aside") continue;
    const last = bands.at(-1);
    if (last?.band === screen.band) last.screens = [...last.screens, screen];
    else
      bands.push({
        band: screen.band,
        label: BAND_LABELS[screen.band],
        screens: [screen],
      });
  }

  return bands;
}
