"use client";

import { CalendarDays, X } from "lucide-react";
import Link from "next/link";

import { SidePanel } from "@/components/atoms/SidePanel";
import { UserAvatar } from "@/components/atoms/UserAvatar";
import { UserActivityTab } from "@/components/organisms/UserActivityTab";
import { UserAuditTab } from "@/components/organisms/UserAuditTab";
import { UserIdentityTab } from "@/components/organisms/UserIdentityTab";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  Role,
  UpdateUserIdentityRequest,
  UserResponse,
} from "@/lib/api/generated/model";
import type { WeekPresence } from "@/lib/presence";

interface UserPanelProps {
  user: UserResponse;
  /** Managing users is reserved for managers. */
  roleModifiable: boolean;
  /** False on one's own account: nobody cuts off their own access. */
  canChangeStatus: boolean;
  /** Writing who a teammate is stays with the managers, like the role. */
  editable: boolean;
  /**
   * True on one's own account alone.
   *
   * Everyone says their own week: where somebody works from is a fact about
   * them, and relaying it through a manager would only put a delay between
   * the fact and the board the team reads.
   */
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
  onClose: () => void;
}

/**
 * A teammate, opened beside the list.
 *
 * Three facets, in that order: who the account is, what the person carries,
 * and everything the register holds on them. « Informations » is what Ganesh
 * decides of an Entra account, and the week the person declares; « Activité »
 * is read and never written; « Journal » is the register, both sides of their
 * id — what they did and what was done to them.
 *
 * The two last are only read once opened: a panel one opens to change a role
 * asks the API for nothing.
 *
 * The list behind stays visible, so one compares two colleagues without
 * walking back through a page each time.
 */
export function UserPanel({
  user,
  roleModifiable,
  canChangeStatus,
  editable,
  isMe,
  onChangeRole,
  onSetActive,
  onUpdateIdentity,
  onDeclarePresence,
  now,
  onClose,
}: UserPanelProps) {
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
        <Tabs defaultValue="identity" className="flex min-h-0 flex-1 flex-col gap-4">
          <TabsList className="shrink-0">
            <TabsTrigger value="identity" className="cursor-pointer">
              Informations
            </TabsTrigger>
            <TabsTrigger value="activity" className="cursor-pointer">
              Activité
            </TabsTrigger>
            <TabsTrigger value="audit" className="cursor-pointer">
              Journal
            </TabsTrigger>
          </TabsList>

          <TabsContent value="identity">
            <UserIdentityTab
              user={user}
              roleModifiable={roleModifiable}
              canChangeStatus={canChangeStatus}
              editable={editable}
              isMe={isMe}
              onChangeRole={onChangeRole}
              onSetActive={onSetActive}
              onUpdateIdentity={onUpdateIdentity}
              onDeclarePresence={onDeclarePresence}
              now={now}
            />
          </TabsContent>

          <TabsContent value="activity">
            <UserActivityTab userId={user.id} now={now} />
          </TabsContent>

          <TabsContent value="audit">
            <UserAuditTab userId={user.id} />
          </TabsContent>
        </Tabs>
      </div>
    </SidePanel>
  );
}
