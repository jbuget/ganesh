"use client";

import { LogOut, UserRound } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { UserResponse } from "@/lib/api/generated/model";
import { roleLabel } from "@/lib/roles";

interface UserMenuProps {
  user: UserResponse;
  onSignOut: () => void | Promise<void>;
  /** Folded, the bar leaves room for the avatar alone. */
  collapsed?: boolean;
}

/**
 * Who is signed in, and the way out.
 *
 * The foot of the sidebar already shows the name: the menu adds what one only
 * looks up in doubt — the exact address, the role that opens or closes actions
 * — and the two things that go nowhere else. « Mon profil » is here rather
 * than in the navigation above, which lists functions of the product: a
 * personal setting read beside « Projets » would pass for one.
 */
export function UserMenu({ user, onSignOut, collapsed = false }: UserMenuProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={`Compte de ${user.display_name}`}
        className={[
          "flex w-full cursor-pointer items-center gap-2.5 border-t border-slate-200 py-3 transition-colors hover:bg-slate-50",
          collapsed ? "justify-center px-0" : "px-4",
        ].join(" ")}
      >
        <span
          aria-hidden="true"
          className="flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-medium text-slate-700"
        >
          {user.initials}
        </span>
        <span className={collapsed ? "sr-only" : "min-w-0 text-left"}>
          <span className="block truncate text-sm">{user.display_name}</span>
          {user.role === "MANAGER" && (
            <span className="block text-xs text-slate-500">{roleLabel(user.role)}</span>
          )}
        </span>
      </PopoverTrigger>

      <PopoverContent align="start" side="top" className="w-64 gap-0 p-0">
        <div className="px-3 py-2.5">
          <p className="truncate text-sm font-semibold">{user.display_name}</p>
          <p className="truncate text-xs text-slate-500">{user.email}</p>
        </div>

        <p className="border-t border-slate-200 px-3 py-2.5 text-sm text-slate-600">
          {roleLabel(user.role)}
        </p>

        <div className="border-t border-slate-200 p-1">
          <Link
            href="/profile"
            onClick={() => setOpen(false)}
            className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
          >
            <UserRound className="size-4 shrink-0 text-slate-500" aria-hidden />
            Mon profil
          </Link>

          <button
            type="button"
            onClick={() => {
              setOpen(false);
              void onSignOut();
            }}
            className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
          >
            <LogOut className="size-4 shrink-0 text-slate-500" aria-hidden />
            Déconnexion
          </button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
