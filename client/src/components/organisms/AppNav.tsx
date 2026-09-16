"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ONGLETS = [
  { href: "/", label: "Activité" },
  { href: "/projets", label: "Projets" },
] as const;

/** Navigation principale : saisie du temps, referentiel des missions. */
export function AppNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Navigation principale" className="border-b border-slate-300">
      <ul className="mx-auto flex max-w-[1600px] gap-1 px-6">
        {ONGLETS.map((onglet) => {
          const actif = pathname === onglet.href;
          return (
            <li key={onglet.href}>
              <Link
                href={onglet.href}
                aria-current={actif ? "page" : undefined}
                className={[
                  "inline-block border-b-2 px-4 py-3 text-sm transition-colors",
                  actif
                    ? "border-slate-900 font-medium text-slate-900"
                    : "border-transparent text-slate-500 hover:text-slate-900",
                ].join(" ")}
              >
                {onglet.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
