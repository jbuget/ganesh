"use client";

import { CalendarDays, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DeactivateUserDialog } from "@/components/atoms/DeactivateUserDialog";
import { InlineTextField } from "@/components/atoms/InlineTextField";
import { OptionPicker } from "@/components/atoms/OptionPicker";
import { RolePicker } from "@/components/atoms/RolePicker";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { SidePanel } from "@/components/atoms/SidePanel";
import { StatusBadge } from "@/components/atoms/StatusBadge";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { UserDeclaredDays } from "@/components/molecules/UserDeclaredDays";
import { UserMissions } from "@/components/molecules/UserMissions";
import { UserMonths } from "@/components/molecules/UserMonths";
import type {
  Role,
  UpdateUserIdentityRequest,
  UserResponse,
} from "@/lib/api/generated/model";
import { useUserRecord } from "@/lib/api/queries";
import { isoDay } from "@/lib/dates";
import { DEPARTMENTS } from "@/lib/departments";
import { ORG_LEVELS } from "@/lib/org-levels";
import { formatParisDateTime } from "@/lib/instants";
import { since } from "@/lib/relative-dates";

interface UserPanelProps {
  user: UserResponse;
  /**
   * Whether this reader may move this account on the ladder.
   *
   * Not « is a manager » any more: nobody changes their own rank, and nobody
   * touches somebody standing above them.
   */
  roleModifiable: boolean;
  /** The ranks this reader may hand out — never above their own. */
  grantable: Role[];
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
 * A teammate, opened beside the list.
 *
 * Two halves, in that order: what the account is, then what the person
 * carries. The first comes from Entra and cannot be edited here — only what
 * Ganesh decides of it, who is behind it, where they work, the role and the
 * access. The second is read and never written: the projects they were put
 * on, where their time went lately, and where their monthly sheets stand.
 * Each of those leads somewhere — a project sheet, a month — because reading
 * the panel is what tells one where to go next.
 *
 * The list behind stays visible, so one compares two colleagues without
 * walking back through a page each time.
 */
export function UserPanel({
  user,
  roleModifiable,
  grantable,
  canChangeStatus,
  editable,
  onChangeRole,
  onSetActive,
  onUpdateIdentity,
  now,
  onClose,
}: UserPanelProps) {
  const [askingDeactivation, setAskingDeactivation] = useState(false);
  // Asked for here rather than by the list: a record is read for the one
  // teammate somebody opened, never for the thirty rows behind.
  const { record, isLoading } = useUserRecord(user.id);

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

        {/* The month is what one goes to next, whether to read it or to fill
            it in for somebody away: everything below says something about it. */}
        <Link
          href={`/timesheet?user=${user.id}`}
          aria-label="Ouvrir sa feuille de temps"
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <CalendarDays className="size-4" aria-hidden />
        </Link>

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
            modifiable={roleModifiable}
            grantable={grantable}
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

        {/* What the account is comes first and is edited here; what the person
            carries follows, and is only read. */}
        <div className="mt-6 space-y-6">
          {isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

          {record && (
            <>
              <section className="space-y-2">
                <SheetSectionTitle>Projets</SheetSectionTitle>
                <UserMissions missions={record.missions} />
              </section>

              <section className="space-y-2">
                <SheetSectionTitle>Temps déclaré</SheetSectionTitle>
                <UserDeclaredDays declared={record.declared} />
              </section>

              <section className="space-y-2">
                <SheetSectionTitle>Feuilles de temps</SheetSectionTitle>
                <UserMonths
                  months={record.months}
                  userId={user.id}
                  today={isoDay(now)}
                />
              </section>
            </>
          )}
        </div>
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
