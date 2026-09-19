"use client";

import {
  CalendarDays,
  ChartNoAxesColumn,
  FolderKanban,
  GanttChartSquare,
  Home,
  KanbanSquare,
  KeyRound,
  PanelLeft,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/atoms/Logo";
import { UserMenu } from "@/components/atoms/UserMenu";
import { Button } from "@/components/ui/button";
import { useSignOut } from "@/lib/use-sign-out";
import { useCurrentUser } from "@/lib/api/queries";
import { toggleSidebar, useSidebarCollapsed } from "@/lib/sidebar-store";

const TABS = [
  // « Accueil » opens the list and holds the root: it is what one lands on
  // after signing in, and it names what to do before the screens that do it.
  { href: "/", label: "Accueil", Icon: Home },
  { href: "/activite", label: "Activité", Icon: CalendarDays },
  { href: "/kanban", label: "Kanban", Icon: KanbanSquare },
  { href: "/projects", label: "Projets", Icon: FolderKanban },
  { href: "/planning", label: "Planification", Icon: GanttChartSquare },
  { href: "/users", label: "Utilisateurs", Icon: Users },
  // Shown to everyone, as « Utilisateurs » is: the navigation says what
  // exists, and the permission lives on the actions.
  { href: "/api-keys", label: "API", Icon: KeyRound },
  // « Statistiques » closes the list, and stays there: it reads the others
  // rather than standing beside them. A new screen goes above it, never after.
  { href: "/stats", label: "Statistiques", Icon: ChartNoAxesColumn },
] as const;

/**
 * Sidebar: navigation at the top, current user at the bottom.
 *
 * It folds into a band of icons to give its width back to the grid, on screens
 * where the month is cramped. The name stays visible as soon as it is
 * unfolded: since anyone may enter a colleague's month, knowing which identity
 * one acts under is no detail.
 */
export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useCurrentUser();
  const collapsed = useSidebarCollapsed();
  const signOut = useSignOut();

  return (
    <aside
      className={[
        // `min-w-0` is essential: a flex child has `min-width: auto` and
        // otherwise refuses to become narrower than its content, cancelling
        // the fold. No transition on the width: `transition-[width]` froze the
        // bar at its starting width, and folding had no visible effect.
        "flex min-w-0 shrink-0 flex-col overflow-hidden border-r border-slate-300 bg-white",
        collapsed ? "w-14" : "w-56",
      ].join(" ")}
    >
      <div
        className={[
          "flex items-center gap-2 px-3 py-4",
          collapsed ? "flex-col gap-3" : "justify-between",
        ].join(" ")}
      >
        <span className="flex min-w-0 items-center gap-2">
          <Logo className="size-6 shrink-0" />
          {/* Folded, the name is still read by screen readers. */}
          <span className={collapsed ? "sr-only" : "min-w-0"}>
            <span className="block text-sm font-semibold tracking-tight">Ganesh</span>
            <span className="block text-xs text-slate-500">WAAT</span>
          </span>
        </span>

        <Button
          variant="ghost"
          size="icon"
          aria-label={
            collapsed ? "Déplier la barre latérale" : "Replier la barre latérale"
          }
          aria-pressed={collapsed}
          title={collapsed ? "Déplier la barre latérale" : "Replier la barre latérale"}
          onClick={toggleSidebar}
        >
          <PanelLeft />
        </Button>
      </div>

      <nav aria-label="Navigation principale" className="flex-1 px-2">
        <ul className="flex flex-col gap-1">
          {TABS.map(({ href, label, Icon }) => {
            const isActive = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={isActive ? "page" : undefined}
                  title={collapsed ? label : undefined}
                  className={[
                    "flex items-center gap-2.5 rounded-md py-2 text-sm transition-colors",
                    collapsed ? "justify-center px-0" : "px-3",
                    isActive
                      ? "bg-slate-100 font-medium text-slate-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                  ].join(" ")}
                >
                  <Icon className="size-4 shrink-0" />
                  {/* Folded, the label is still read by screen readers. */}
                  <span className={collapsed ? "sr-only" : undefined}>{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {user && <UserMenu user={user} collapsed={collapsed} onSignOut={signOut} />}
    </aside>
  );
}
