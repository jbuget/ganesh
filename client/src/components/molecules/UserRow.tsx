"use client";

import { useState } from "react";

import { DeactivateUserDialog } from "@/components/atoms/DeactivateUserDialog";
import { RolePicker } from "@/components/atoms/RolePicker";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { TableCell, TableRow } from "@/components/ui/table";
import type { Role, UserResponse } from "@/lib/api/generated/model";
import { depuis } from "@/lib/dates-relatives";

interface UserRowProps {
  user: UserResponse;
  /** La gestion des utilisateurs est reservee aux managers. */
  roleModifiable: boolean;
  /** Faux sur sa propre ligne : nul ne coupe son propre acces. */
  statutModifiable: boolean;
  onChangeRole: (userId: number, role: Role) => void | Promise<void>;
  onSetActive: (userId: number, is_active: boolean) => void | Promise<void>;
  /** Injecte : un rendu date par `new Date()` ne se testerait pas. */
  maintenant: Date;
}

/** Un utilisateur : qui il est, ce qu'il peut faire, quand il est passe. */
export function UserRow({
  user,
  roleModifiable,
  statutModifiable,
  onChangeRole,
  onSetActive,
  maintenant,
}: UserRowProps) {
  const [coupureADemander, setCoupureADemander] = useState(false);

  return (
    <TableRow className={user.is_active ? undefined : "text-slate-400"}>
      <TableCell className="py-2">
        <span className="flex items-center gap-2.5">
          <UserAvatar
            initials={user.initials}
            name={user.display_name}
            attenue={!user.is_active}
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
        {/* Un compte jamais venu n'est pas « il y a longtemps » : il n'est jamais venu. */}
        {user.last_login_at ? (
          <span title={new Date(user.last_login_at).toLocaleString("fr-FR")}>
            {depuis(user.last_login_at, maintenant)}
          </span>
        ) : (
          <span className="text-slate-400">Jamais</span>
        )}
      </TableCell>

      <TableCell className="py-2">
        <StatusBadge
          is_active={user.is_active}
          modifiable={statutModifiable}
          // Couper un acces se confirme ; le retablir ne retire rien a personne.
          onToggle={(is_active) =>
            is_active ? onSetActive(user.id, true) : setCoupureADemander(true)
          }
        />

        <DeactivateUserDialog
          open={coupureADemander}
          onOpenChange={setCoupureADemander}
          name={user.display_name}
          onConfirm={() => {
            setCoupureADemander(false);
            return onSetActive(user.id, false);
          }}
        />
      </TableCell>
    </TableRow>
  );
}
