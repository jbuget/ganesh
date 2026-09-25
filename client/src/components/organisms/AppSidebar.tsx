"use client";

import { PanelLeft, Search } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/atoms/Logo";
import { UserMenu } from "@/components/atoms/UserMenu";
import { NotificationPanel } from "@/components/organisms/NotificationPanel";
import { Button } from "@/components/ui/button";
import { openPalette, useShortcutHint } from "@/lib/command-palette-store";
import { screensFor } from "@/lib/navigation";
import { useNavigationTrail } from "@/lib/navigation-trail";
import { useSignOut } from "@/lib/use-sign-out";
import { useCurrentUser } from "@/lib/api/queries";
import { toggleSidebar, useSidebarCollapsed } from "@/lib/sidebar-store";

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
  // Recorded from here rather than from each screen: the bar is mounted once,
  // above them all, and therefore notes the arrival before the screen reached
  // asks where it came from.
  useNavigationTrail();
  const { user } = useCurrentUser();
  const collapsed = useSidebarCollapsed();
  const signOut = useSignOut();
  const shortcut = useShortcutHint();

  return (
    <aside
      className={[
        // `min-w-0` is essential: a flex child has `min-width: auto` and
        // otherwise refuses to become narrower than its content, cancelling
        // the fold. No transition on the width: `transition-[width]` froze the
        // bar at its starting width, and folding had no visible effect.
        "flex min-w-0 shrink-0 flex-col overflow-hidden border-r border-slate-300 bg-white",
        // Held to the height of the window, like the screen it stands beside:
        // `PageLayout` is `h-screen` and scrolls its own content, so the bar
        // is measured the same way rather than growing with the page. On a
        // short screen its foot — the bell, the name, the way out — used to
        // sit below the fold with no way to reach it.
        "h-screen",
        collapsed ? "w-14" : "w-56",
      ].join(" ")}
    >
      <div
        className={[
          "flex shrink-0 items-center gap-2 px-3 py-4",
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

      {/* Above the tabs, where one reads before choosing: the palette leads
          to the same screens and to what is inside them, and a shortcut
          nobody is shown is a shortcut nobody uses. */}
      <div className="shrink-0 px-2 pb-2">
        <button
          type="button"
          onClick={openPalette}
          title={collapsed ? `Rechercher (${shortcut})` : undefined}
          aria-label={`Rechercher (${shortcut})`}
          className={[
            "flex w-full cursor-pointer items-center gap-2.5 rounded-md border border-slate-300 py-1.5 text-sm text-slate-500 transition-colors hover:border-slate-400 hover:text-slate-800",
            collapsed ? "justify-center px-0" : "px-3",
          ].join(" ")}
        >
          <Search className="size-4 shrink-0" aria-hidden />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">Rechercher</span>
              <kbd className="shrink-0 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-sans text-[11px] text-slate-400">
                {shortcut}
              </kbd>
            </>
          )}
        </button>
      </div>

      {/* The one part of the bar that scrolls: the tabs. `min-h-0` is what
          lets it, a flex child refusing by default to shrink under its own
          content — without it the list would push the foot out of the window
          instead of overflowing. */}
      <nav
        aria-label="Navigation principale"
        className="min-h-0 flex-1 overflow-y-auto px-2"
      >
        <ul className="flex flex-col gap-1">
          {screensFor(user?.role).map(({ href, label, Icon }) => {
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

      {/* The bell sits just above the name, where one already looks to know
          which identity one is acting under. It is deliberately not a tab: the
          navigation lists what the team shares, and an inbox belongs to one
          person. « Tout voir » is what leads to the page. */}
      {user && (
        <div className="shrink-0 border-t border-slate-200 px-2 py-1.5">
          <NotificationPanel collapsed={collapsed} />
        </div>
      )}

      {user && (
        <div className="shrink-0">
          <UserMenu user={user} collapsed={collapsed} onSignOut={signOut} />
        </div>
      )}
    </aside>
  );
}
