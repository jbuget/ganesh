"use client";

import { RolePicker } from "@/components/atoms/RolePicker";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { TableCell, TableRow } from "@/components/ui/table";
import type { Role, UserResponse } from "@/lib/api/generated/model";
import { depuis } from "@/lib/dates-relatives";

interface UserRowProps {
  user: UserResponse;
  /** La gestion des utilisateurs est reservee aux managers. */
  roleModifiable: boolean;
  onChangeRole: (userId: number, role: Role) => void | Promise<void>;
  /** Injecte : un rendu date par `new Date()` ne se testerait pas. */
  maintenant: Date;
}

/** Un utilisateur : qui il est, ce qu'il peut faire, quand il est passe. */
export function UserRow({
  user,
  roleModifiable,
  onChangeRole,
  maintenant,
}: UserRowProps) {
  return (
    <TableRow className={user.actif ? undefined : "text-slate-400"}>
      <TableCell className="py-2">
        <span className="flex items-center gap-2.5">
          <UserAvatar
            initiales={user.initiales}
            nom={user.display_name}
            attenue={!user.actif}
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
        {user.derniere_connexion ? (
          <span title={new Date(user.derniere_connexion).toLocaleString("fr-FR")}>
            {depuis(user.derniere_connexion, maintenant)}
          </span>
        ) : (
          <span className="text-slate-400">Jamais</span>
        )}
      </TableCell>

      <TableCell className="py-2">
        {/* Un compte actif est la norme : seul l'ecart se dit. */}
        {!user.actif && (
          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-500">
            Inactif
          </span>
        )}
      </TableCell>
    </TableRow>
  );
}
