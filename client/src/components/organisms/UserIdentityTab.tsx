"use client";

import { useState } from "react";

import { DeactivateUserDialog } from "@/components/atoms/DeactivateUserDialog";
import { InlineTextField } from "@/components/atoms/InlineTextField";
import { OptionPicker } from "@/components/atoms/OptionPicker";
import { RolePicker } from "@/components/atoms/RolePicker";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { PresenceWeek } from "@/components/molecules/PresenceWeek";
import type {
  Role,
  UpdateUserIdentityRequest,
  UserResponse,
} from "@/lib/api/generated/model";
import { DEPARTMENTS } from "@/lib/departments";
import { ORG_LEVELS } from "@/lib/org-levels";
import { formatParisDateTime } from "@/lib/instants";
import { type WeekPresence, weekOf } from "@/lib/presence";
import { since } from "@/lib/relative-dates";

interface UserIdentityTabProps {
  user: UserResponse;
  /**
   * The roles the person reading may hand this account. Empty when they may
   * hand none — a teammate reading, or a manager reading an admin's row.
   */
  assignableRoles: Role[];
  /** False on one's own account: nobody cuts off their own access. */
  canChangeStatus: boolean;
  /** Writing who a teammate is stays with the managers, like the role. */
  editable: boolean;
  /** True on one's own account alone: everyone says their own week. */
  isMe: boolean;
  onChangeRole: (userId: number, role: Role) => void | Promise<void>;
  onSetActive: (userId: number, is_active: boolean) => void | Promise<void>;
  onUpdateIdentity: (
    user: UserResponse,
    change: UpdateUserIdentityRequest,
  ) => void | Promise<void>;
  onDeclarePresence: (week: WeekPresence) => void | Promise<void>;
  /** Injected: a render dated by `new Date()` could not be tested. */
  now: Date;
}

/**
 * Who the account is, and the week the person says they work.
 *
 * The account comes from Entra and cannot be edited here — only what Ganesh
 * decides of it: who is behind it, where they work, the role and the access.
 * The week is the one thing on this panel the person writes themselves.
 */
export function UserIdentityTab({
  user,
  assignableRoles,
  canChangeStatus,
  editable,
  isMe,
  onChangeRole,
  onSetActive,
  onUpdateIdentity,
  onDeclarePresence,
  now,
}: UserIdentityTabProps) {
  const [askingDeactivation, setAskingDeactivation] = useState(false);

  return (
    <div>
      <SheetSectionTitle>Compte</SheetSectionTitle>

      <SheetRow title="Email">
        {/* First, because it is the only thing that never moves: Entra's
            address identifies the account, everything below describes who
            holds it. */}
        <span className="text-sm text-slate-700">{user.email}</span>
      </SheetRow>

      <SheetRow title="Prénom">
        <InlineTextField
          value={user.first_name}
          label="Prénom"
          editable={editable}
          onChange={(first_name) => onUpdateIdentity(user, { first_name })}
        />
      </SheetRow>

      <SheetRow title="Nom">
        <InlineTextField
          value={user.last_name}
          label="Nom"
          editable={editable}
          onChange={(last_name) => onUpdateIdentity(user, { last_name })}
        />
      </SheetRow>

      <SheetRow title="GitHub">
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
      </SheetRow>

      <SheetRow title="Département">
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
      </SheetRow>

      <SheetRow title="Niveau">
        {/* Where the person sits in the company, beside where they work.
            Left blank for most: it is filled in for whoever has to be told
            apart, which today means the COMEX a need is carried to. It says
            nothing about what they may do here — the role below does, and
            the two never agree with each other. */}
        <OptionPicker
          value={user.org_level}
          options={ORG_LEVELS}
          label="Niveau"
          editable={editable}
          onChange={(org_level) => onUpdateIdentity(user, { org_level })}
        />
      </SheetRow>

      <SheetRow title="Rôle">
        <RolePicker
          role={user.role}
          choices={assignableRoles}
          onChange={(role) => onChangeRole(user.id, role)}
        />
      </SheetRow>

      <SheetRow title="Statut">
        <StatusBadge
          is_active={user.is_active}
          modifiable={canChangeStatus}
          // Cutting off access is confirmed; restoring it takes nothing from
          // anyone.
          onToggle={(is_active) =>
            is_active ? onSetActive(user.id, true) : setAskingDeactivation(true)
          }
        />
      </SheetRow>

      <SheetRow title="Dernière connexion">
        {/* An account that never came is not « long ago »: it never came. */}
        {user.last_login_at ? (
          <span className="text-sm text-slate-700">
            {since(user.last_login_at, now)}
            <span className="ml-2 text-xs text-slate-400">
              {formatParisDateTime(user.last_login_at)}
            </span>
          </span>
        ) : (
          <span className="text-sm text-slate-400">Jamais</span>
        )}
      </SheetRow>

      {/* After the account: their ordinary week is not part of it — it is what
          they tell the team about themselves, and the only thing on this panel
          they write. */}
      <section className="mt-6 space-y-2">
        <SheetSectionTitle>Présence</SheetSectionTitle>
        <PresenceWeek
          week={weekOf(user.presence)}
          editable={isMe}
          onChange={onDeclarePresence}
        />
      </section>

      <DeactivateUserDialog
        open={askingDeactivation}
        onOpenChange={setAskingDeactivation}
        name={user.display_name}
        onConfirm={() => {
          setAskingDeactivation(false);
          return onSetActive(user.id, false);
        }}
      />
    </div>
  );
}
