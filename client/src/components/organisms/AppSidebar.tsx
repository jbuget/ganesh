"use client";

import { CalendarDays, FolderKanban, PanelLeft } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/lib/api/queries";
import { basculerBarreLaterale, useBarreLateraleRepliee } from "@/lib/sidebar-store";

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
 * Elle se replie en une bande d'icones pour rendre sa largeur au tableau, sur
 * les ecrans ou le mois est a l'etroit. Le nom reste visible des qu'elle est
 * depliee : chacun pouvant saisir le mois d'un collegue, savoir sous quelle
 * identite on agit n'est pas un detail.
 */
export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useCurrentUser();
  const repliee = useBarreLateraleRepliee();

  return (
    <aside
      className={[
        // `min-w-0` est indispensable : un enfant flex a `min-width: auto` et refuse
        // sinon de devenir plus etroit que son contenu, annulant le repli.
        // Pas de transition sur la largeur : `transition-[width]` figeait la barre a
        // sa largeur de depart, le repli n'avait aucun effet visible.
        "flex min-w-0 shrink-0 flex-col overflow-hidden border-r border-slate-300 bg-white",
        repliee ? "w-14" : "w-56",
      ].join(" ")}
    >
      <div
        className={[
          "flex items-center gap-2 px-3 py-4",
          repliee ? "justify-center" : "justify-between",
        ].join(" ")}
      >
        {!repliee && (
          <span className="min-w-0">
            <span className="block text-sm font-semibold tracking-tight">
              Timesheet
            </span>
            <span className="block text-xs text-slate-500">WAAT</span>
          </span>
        )}

        <Button
          variant="ghost"
          size="icon"
          aria-label={
            repliee ? "Déplier la barre latérale" : "Replier la barre latérale"
          }
          aria-pressed={repliee}
          title={repliee ? "Déplier la barre latérale" : "Replier la barre latérale"}
          onClick={basculerBarreLaterale}
        >
          <PanelLeft />
        </Button>
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
                  title={repliee ? label : undefined}
                  className={[
                    "flex items-center gap-2.5 rounded-md py-2 text-sm transition-colors",
                    repliee ? "justify-center px-0" : "px-3",
                    actif
                      ? "bg-slate-100 font-medium text-slate-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                  ].join(" ")}
                >
                  <Icone className="size-4 shrink-0" />
                  {/* Replie, le libelle reste lu par les lecteurs d'ecran. */}
                  <span className={repliee ? "sr-only" : undefined}>{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {user && (
        <div
          className={[
            "flex items-center gap-2.5 border-t border-slate-200 py-3",
            repliee ? "justify-center px-0" : "px-4",
          ].join(" ")}
        >
          <span
            aria-hidden="true"
            title={repliee ? user.display_name : undefined}
            className="flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-700"
          >
            {initiales(user.display_name)}
          </span>
          <span className={repliee ? "sr-only" : "min-w-0"}>
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
