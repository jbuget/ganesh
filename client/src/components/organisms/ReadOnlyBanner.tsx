"use client";

import { Eye } from "lucide-react";

import { useMayWrite } from "@/lib/use-may-write";

/**
 * The band a guest reads above every screen, and nobody else ever sees.
 *
 * It sits in the frame for the reason the command palette does: it belongs to
 * no screen in particular and to all of them. Said once, there, rather than on
 * each gesture — a guest meets a dozen screens, and every one of them would
 * otherwise have to explain itself.
 *
 * It names what is missing — rights — and who hands them out: « refusé » with
 * no way forward is a dead end.
 */
export function ReadOnlyBanner() {
  if (useMayWrite()) return null;

  return (
    <div
      role="status"
      className="flex items-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900"
    >
      <Eye className="size-4 shrink-0" aria-hidden />
      <span>
        Votre compte lit Ganesh sans y écrire. Demandez vos droits à un manager pour
        saisir vos temps.
      </span>
    </div>
  );
}
