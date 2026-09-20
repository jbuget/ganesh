"use client";

import { StatusBadge } from "@/components/atoms/StatusBadge";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { TableCell, TableRow } from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";
import { formatParisDateTime } from "@/lib/instants";
import { since } from "@/lib/relative-dates";
import { roleLabel } from "@/lib/roles";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface UserRowProps {
  user: UserResponse;
  /** Injected: a render dated by `new Date()` could not be tested. */
  now: Date;
  onOpen: () => void;
}

/**
 * A user: who they are, what they may do, when they last came by.
 *
 * The row compares, it does not edit: like the mission reference list, it opens
 * one thing only — the panel, where the role and the access are given away.
 * Editing in two places would multiply the paths to the same data.
 */
export function UserRow({ user, now, onOpen }: UserRowProps) {
  return (
    // The row takes the page background, the name cell white: the teammate
    // reads as the anchor of the line rather than as its first column. The cell
    // follows the row one step behind — page background where it goes a shade
    // darker — so hovering marks the whole line without flattening the relief.
    <TableRow
      onClick={onOpen}
      className={`group cursor-pointer bg-slate-50 hover:bg-slate-100 ${
        user.is_active ? "" : "text-slate-400"
      }`}
    >
      <TableCell
        className={`bg-white py-2 group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        <span className="flex items-center gap-2.5">
          <UserAvatar
            initials={user.initials}
            name={user.display_name}
            dimmed={!user.is_active}
          />
          {/* The whole row responds to the mouse; this button gives the same
              opening to the keyboard, without opening twice. */}
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onOpen();
            }}
            className="min-w-0 cursor-pointer truncate text-left font-medium"
          >
            {user.display_name}
          </button>
        </span>
      </TableCell>

      <TableCell className="py-2 text-slate-500">{user.email}</TableCell>

      <TableCell className="py-2 text-slate-500">
        {/* The handle alone, as it is stored: the row compares the team, it
            does not walk off to GitHub. */}
        {user.github_username ?? <span className="text-slate-400">—</span>}
      </TableCell>

      <TableCell className="py-2 text-slate-600">{roleLabel(user.role)}</TableCell>

      <TableCell className="py-2 text-slate-500">
        {/* An account that never came is not « long ago »: it never came. */}
        {user.last_login_at ? (
          <span title={formatParisDateTime(user.last_login_at)}>
            {since(user.last_login_at, now)}
          </span>
        ) : (
          <span className="text-slate-400">Jamais</span>
        )}
      </TableCell>

      <TableCell className="py-2">
        <StatusBadge is_active={user.is_active} modifiable={false} />
      </TableCell>
    </TableRow>
  );
}
