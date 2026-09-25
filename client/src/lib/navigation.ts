import {
  CalendarDays,
  ChartNoAxesColumn,
  Cog,
  FolderKanban,
  GanttChartSquare,
  Home,
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

export interface Screen {
  href: string;
  label: string;
  Icon: LucideIcon;
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
 * Written once: the sidebar lists them and the palette leads to them, and two
 * lists of the same screens would end up disagreeing about what exists.
 */
export const SCREENS: readonly Screen[] = [
  // « Accueil » opens the list and holds the root: it is what one lands on
  // after signing in, and it names what to do before the screens that do it.
  { href: "/", label: "Accueil", Icon: Home },
  { href: "/timesheet", label: "Saisie des temps", Icon: CalendarDays },
  { href: "/kanban", label: "Kanban", Icon: KanbanSquare },
  { href: "/projects", label: "Projets", Icon: FolderKanban },
  { href: "/activity-summary", label: "Synthèse d'activité", Icon: TableProperties },
  { href: "/planning", label: "Planification", Icon: GanttChartSquare },
  { href: "/roadmap", label: "Feuille de route", Icon: Milestone },
  { href: "/gazette", label: "La Gazette", Icon: Newspaper },
  { href: "/users", label: "Utilisateurs", Icon: Users },
  { href: "/mood", label: "Moral", Icon: Smile },
  // Shown to everyone, as « Utilisateurs » is: the navigation says what
  // exists, and the permission lives on the actions.
  { href: "/api-mcp", label: "API / MCP", Icon: KeyRound },
  // The register read across, where a mission's « Journal » tab reads one
  // mission's. Same word for the same thing, and the only screen a deleted
  // project can still be found from: its lines outlive it, with no mission
  // left to open them in.
  { href: "/logs", label: "Journal", Icon: ScrollText },
  // « Statistiques » closes the list, and stays there: it reads the others
  // rather than standing beside them. A new screen goes above it, never after.
  { href: "/stats", label: "Statistiques", Icon: ChartNoAxesColumn },
  // Below « Statistiques », which closes the list of screens one works in:
  // this one is not one of them. It is about the platform, not about the
  // missions, and only an administrator sees it at all.
  {
    href: "/admin",
    label: "Administration",
    Icon: Cog,
    seenFrom: "ADMIN",
  },
] as const;

/** The screens a given role is shown. */
export function screensFor(role: Role | undefined): readonly Screen[] {
  return SCREENS.filter((screen) => !screen.seenFrom || holds(role, screen.seenFrom));
}
