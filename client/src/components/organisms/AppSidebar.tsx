"use client";

import { CalendarDays, FolderKanban } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCurrentUser } from "@/lib/api/queries";

const ONGLETS = [
  { href: "/", label: "Activité", Icone: CalendarDays },
  { href: "/projets", label: "Projets", Icone: FolderKanban },
] as const;

/** Initiales d'un nom, pour la pastille du pied de barre. */
function initiales(nom: string): string {
  return nom
    .split(/[\s.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((mot) => mot[0]?.toUpperCase() ?? "")
    .join("");
}

/**
 * Barre laterale : navigation en haut, utilisateur courant en bas.
 *
 * Le nom reste visible en permanence : chacun pouvant saisir le mois d'un
 * collegue, savoir sous quelle identite on agit n'est pas un detail.
 */
export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useCurrentUser();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-slate-300 bg-white">
      <div className="px-4 py-5">
        <span className="text-sm font-semibold tracking-tight">Timesheet</span>
        <span className="block text-xs text-slate-500">WAAT</span>
      </div>

      <nav aria-label="Navigation principale" className="flex-1 px-2">
        <ul className="flex flex-col gap-1">
          {ONGLETS.map(({ href, label, Icone }) => {
            const actif = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={actif ? "page" : undefined}
                  className={[
                    "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                    actif
                      ? "bg-slate-100 font-medium text-slate-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                  ].join(" ")}
                >
                  <Icone className="size-4" />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {user && (
        <div className="flex items-center gap-2.5 border-t border-slate-200 px-4 py-3">
          <span
            aria-hidden="true"
            className="flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-700"
          >
            {initiales(user.display_name)}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm">{user.display_name}</span>
            {user.role === "MANAGER" && (
              <span className="block text-xs text-slate-500">Manager</span>
            )}
          </span>
        </div>
      )}
    </aside>
  );
}
