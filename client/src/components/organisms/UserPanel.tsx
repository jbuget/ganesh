"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { DeactivateUserDialog } from "@/components/atoms/DeactivateUserDialog";
import { InlineTextField } from "@/components/atoms/InlineTextField";
import { OptionPicker } from "@/components/atoms/OptionPicker";
import { RolePicker } from "@/components/atoms/RolePicker";
import { SidePanel } from "@/components/atoms/SidePanel";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import type {
  Role,
  UpdateUserIdentityRequest,
  UserResponse,
} from "@/lib/api/generated/model";
import { DEPARTMENTS } from "@/lib/departments";
import { since } from "@/lib/relative-dates";

interface UserPanelProps {
  user: UserResponse;
  /** Managing users is reserved for managers. */
  roleModifiable: boolean;
  /** False on one's own account: nobody cuts off their own access. */
  canChangeStatus: boolean;
  /** Writing who a teammate is stays with the managers, like the role. */
  editable: boolean;
  onChangeRole: (userId: number, role: Role) => void | Promise<void>;
  onSetActive: (userId: number, is_active: boolean) => void | Promise<void>;
  onUpdateIdentity: (
    user: UserResponse,
    change: UpdateUserIdentityRequest,
  ) => void | Promise<void>;
  /** Injected: a render dated by `new Date()` could not be tested. */
  now: Date;
  onClose: () => void;
}

/**
 * One row of the sheet: its heading on the left, its value on the right.
 *
 * The same grammar as the mission sheet — a constant heading width gives the
 * top-to-bottom scan something to lean on.
 */
function Row({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="w-36 shrink-0 pt-0.5 text-sm text-slate-500">{title}</span>
      <div className="min-w-0 flex-1 text-sm">{children}</div>
    </div>
  );
}

/**
 * A teammate, opened beside the list.
 *
 * What one reads about an account comes from Entra and cannot be edited here:
 * only what Ganesh decides — who is behind it, where they work, the role and
 * the access — is given away. The list
 * behind stays visible, so one compares two colleagues without walking back
 * through a page each time.
 */
export function UserPanel({
  user,
  roleModifiable,
  canChangeStatus,
  editable,
  onChangeRole,
  onSetActive,
  onUpdateIdentity,
  now,
  onClose,
}: UserPanelProps) {
  const [askingDeactivation, setAskingDeactivation] = useState(false);

  return (
    <SidePanel label={user.display_name} onClose={onClose}>
      <header className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <UserAvatar
          initials={user.initials}
          name={user.display_name}
          dimmed={!user.is_active}
        />
        <h2 className="min-w-0 flex-1 truncate text-lg font-semibold text-slate-900">
          {user.display_name}
        </h2>

        <button
          type="button"
          aria-label="Fermer"
          onClick={onClose}
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="size-4" aria-hidden />
        </button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 py-4">
        <Row title="Email">
          {/* First, because it is the only thing that never moves: Entra's
              address identifies the account, everything below describes who
              holds it. */}
          <span className="text-slate-700">{user.email}</span>
        </Row>

        <Row title="Prénom">
          <InlineTextField
            value={user.first_name}
            label="Prénom"
            editable={editable}
            onChange={(first_name) => onUpdateIdentity(user, { first_name })}
          />
        </Row>

        <Row title="Nom">
          <InlineTextField
            value={user.last_name}
            label="Nom"
            editable={editable}
            onChange={(last_name) => onUpdateIdentity(user, { last_name })}
          />
        </Row>

        <Row title="GitHub">
          {/* The handle alone: the prefix says the address is already known,
              and what is asked for is the part that completes it. */}
          <InlineTextField
            value={user.github_username}
            label="GitHub"
            prefix="github.com/"
            placeholder="identifiant"
            editable={editable}
            onChange={(github_username) => onUpdateIdentity(user, { github_username })}
          />
        </Row>

        <Row title="Département">
          {/* One department, where a mission may serve several: one works in a
              department, one does not belong to two. The list is the missions'
              own — steering compares the two sides, and could not if the names
              drifted apart. */}
          <OptionPicker
            value={user.department}
            options={DEPARTMENTS}
            label="Département"
            editable={editable}
            onChange={(department) => onUpdateIdentity(user, { department })}
          />
        </Row>

        <Row title="Rôle">
          <RolePicker
            role={user.role}
            modifiable={roleModifiable}
            onChange={(role) => onChangeRole(user.id, role)}
          />
        </Row>

        <Row title="Statut">
          <StatusBadge
            is_active={user.is_active}
            modifiable={canChangeStatus}
            // Cutting off access is confirmed; restoring it takes nothing from
            // anyone.
            onToggle={(is_active) =>
              is_active ? onSetActive(user.id, true) : setAskingDeactivation(true)
            }
          />
        </Row>

        <Row title="Dernière connexion">
          {/* An account that never came is not « long ago »: it never came. */}
          {user.last_login_at ? (
            <span className="text-slate-700">
              {since(user.last_login_at, now)}
              <span className="ml-2 text-xs text-slate-400">
                {new Date(user.last_login_at).toLocaleString("fr-FR")}
              </span>
            </span>
          ) : (
            <span className="text-slate-400">Jamais</span>
          )}
        </Row>
      </div>

      <DeactivateUserDialog
        open={askingDeactivation}
        onOpenChange={setAskingDeactivation}
        name={user.display_name}
        onConfirm={() => {
          setAskingDeactivation(false);
          return onSetActive(user.id, false);
        }}
      />
    </SidePanel>
  );
}
