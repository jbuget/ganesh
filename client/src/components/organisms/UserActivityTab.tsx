"use client";

import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { UserDeclaredDays } from "@/components/molecules/UserDeclaredDays";
import { UserMissions } from "@/components/molecules/UserMissions";
import { UserMonths } from "@/components/molecules/UserMonths";
import { useUserRecord } from "@/lib/api/queries";
import { isoDay } from "@/lib/dates";

interface UserActivityTabProps {
  userId: number;
  /** Injected: a render dated by `new Date()` could not be tested. */
  now: Date;
}

/**
 * What the person carries, read and never written.
 *
 * The projects they were put on, where their time went lately, and where their
 * monthly sheets stand. Each of those leads somewhere — a project sheet, a
 * month — because reading the panel is what tells one where to go next.
 *
 * The record is asked for here rather than by the panel: it is read for the
 * one teammate somebody opened, and only once they ask what that teammate has
 * been doing.
 */
export function UserActivityTab({ userId, now }: UserActivityTabProps) {
  const { record, isLoading } = useUserRecord(userId);

  if (isLoading) return <p className="text-sm text-slate-500">Chargement…</p>;
  if (!record) return null;

  return (
    <div className="space-y-6">
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
        <UserMonths months={record.months} userId={userId} today={isoDay(now)} />
      </section>
    </div>
  );
}
