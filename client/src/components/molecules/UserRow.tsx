"use client";

import { useState } from "react";

import { DeactivateUserDialog } from "@/components/atoms/DeactivateUserDialog";
import { RolePicker } from "@/components/atoms/RolePicker";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { TableCell, TableRow } from "@/components/ui/table";
import type { Role, UserResponse } from "@/lib/api/generated/model";
import { since } from "@/lib/relative-dates";

interface UserRowProps {
  user: UserResponse;
  /** Managing users is reserved for managers. */
  roleModifiable: boolean;
  /** False on one's own row: nobody cuts off their own access. */
  canChangeStatus: boolean;
  onChangeRole: (userId: number, role: Role) => void | Promise<void>;
  onSetActive: (userId: number, is_active: boolean) => void | Promise<void>;
  /** Injected: a render dated by `new Date()` could not be tested. */
  now: Date;
}

/** A user: who they are, what they may do, when they last came by. */
export function UserRow({
  user,
  roleModifiable,
  canChangeStatus,
  onChangeRole,
  onSetActive,
  now,
}: UserRowProps) {
  const [askingDeactivation, setAskingDeactivation] = useState(false);

  return (
    <TableRow className={user.is_active ? undefined : "text-slate-400"}>
      <TableCell className="py-2">
        <span className="flex items-center gap-2.5">
          <UserAvatar
            initials={user.initials}
            name={user.display_name}
            dimmed={!user.is_active}
          />
          <span className="min-w-0 truncate font-medium">{user.display_name}</span>
        </span>
      </TableCell>

      <TableCell className="py-2 text-slate-500">{user.email}</TableCell>

      <TableCell className="py-2">
        <RolePicker
          role={user.role}
          modifiable={roleModifiable}
          onChange={(role) => onChangeRole(user.id, role)}
        />
      </TableCell>

      <TableCell className="py-2 text-slate-500">
        {/* An account that never came is not « long ago »: it never came. */}
        {user.last_login_at ? (
          <span title={new Date(user.last_login_at).toLocaleString("fr-FR")}>
            {since(user.last_login_at, now)}
          </span>
        ) : (
          <span className="text-slate-400">Jamais</span>
        )}
      </TableCell>

      <TableCell className="py-2">
        <StatusBadge
          is_active={user.is_active}
          modifiable={canChangeStatus}
          // Cutting off access is confirmed; restoring it takes nothing from
          // anyone.
          onToggle={(is_active) =>
            is_active ? onSetActive(user.id, true) : setAskingDeactivation(true)
          }
        />

        <DeactivateUserDialog
          open={askingDeactivation}
          onOpenChange={setAskingDeactivation}
          name={user.display_name}
          onConfirm={() => {
            setAskingDeactivation(false);
            return onSetActive(user.id, false);
          }}
        />
      </TableCell>
    </TableRow>
  );
}
