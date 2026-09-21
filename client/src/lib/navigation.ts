import {
  CalendarDays,
  ChartNoAxesColumn,
  FolderKanban,
  GanttChartSquare,
  Home,
  KanbanSquare,
  KeyRound,
  Milestone,
  Newspaper,
  Smile,
  TableProperties,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface Screen {
  href: string;
  label: string;
  Icon: LucideIcon;
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
  // « Statistiques » closes the list, and stays there: it reads the others
  // rather than standing beside them. A new screen goes above it, never after.
  { href: "/stats", label: "Statistiques", Icon: ChartNoAxesColumn },
] as const;
