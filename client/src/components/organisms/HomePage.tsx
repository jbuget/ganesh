"use client";

import Link from "next/link";
import { useMemo } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { MissionCard } from "@/components/molecules/MissionCard";
import { MonthBriefing } from "@/components/molecules/MonthBriefing";
import { MoodCheckIn } from "@/components/molecules/MoodCheckIn";
import { UpdateFeedItem } from "@/components/molecules/UpdateFeedItem";
import { PageLayout } from "@/components/organisms/PageLayout";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { useHome } from "@/lib/use-home";
import { useMood } from "@/lib/use-mood";
import { useOpenedMission } from "@/lib/opened-mission";

/**
 * The screen one lands on: what is waiting, and what one is working on.
 *
 * Ganesh is the one invoked at the opening of every undertaking, and this is
 * where a month opens — the month behind still to close, the missions running,
 * the news published on them since one last looked.
 *
 * It hands over rather than acting: the grid for time, the mission panel for
 * the rest. Keeping it that way is what stops it from slowly becoming a second
 * Saisie des temps.
 *
 * The mood is the one exception, and it is a deliberate one. Answering is a
 * one-second gesture on a window that closes the next working day; behind a
 * link, it would simply never be made, and a morale nobody posts measures
 * nothing. It sits at the head of the right-hand column, where one reads at
 * one's own pace: the left column is the month and what it still owes, and a
 * question about the day has no business pushing that down.
 */
export function HomePage() {
  const home = useHome();
  const mood = useMood();
  const panel = useOpenedMission();
  const now = useMemo(() => new Date(), []);

  const firstName = home.me?.display_name.split(" ")[0];

  return (
    <PageLayout
      header={
        <PageHeader
          title="Accueil"
          subtitle={
            firstName
              ? `Bonjour ${firstName}, voici ce qui vous attend et où en sont vos projets.`
              : "Ce qui vous attend, et où en sont vos projets."
          }
        />
      }
    >
      <div className="grid items-start gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/*
            Nothing shows until the months have arrived. Every block on this
            side reads « nothing to report » from an empty answer — « Tout est à
            jour », « Aucun projet » — and rendering them while the figures are
            still zero would state the opposite of what is being loaded.
          */}
          {home.isLoading ? (
            <p className="text-muted-foreground text-sm">Chargement…</p>
          ) : (
            <>
              <MonthBriefing
                cursor={home.cursor}
                actualDays={home.actualDays}
                forecastDays={home.forecastDays}
                workingDays={home.workingDays}
                monthsToSettle={home.monthsToSettle}
                daysMissing={home.daysMissing}
                missionsToDeclare={home.missionsToDeclare}
              />

              <section>
                <h2 className="mb-3 text-sm font-semibold text-slate-900">
                  Mes projets
                </h2>

                {home.mine.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
                    Aucun projet ne vous est assigné et vous n&apos;avez déclaré aucun
                    temps récemment.{" "}
                    <Link
                      href="/projects"
                      className="cursor-pointer font-medium text-sky-700 hover:underline"
                    >
                      Parcourir les projets
                    </Link>
                  </p>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                    {home.mine.map((mission) => (
                      <MissionCard
                        key={mission.item.project.id}
                        mission={mission}
                        onOpen={(projectId) => panel.open(projectId)}
                      />
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </div>

        {/* The right-hand column keeps to itself: it is read down, at one's own
          pace, while the left column is scanned. Mixing the two would make the
          reminders scroll past what one came to do. */}
        <aside className="space-y-4">
          {/* First, and outside the wait the left column is held by: the mood
            carries its own query, and holding it behind four grids would close
            the window on whoever lands while they are still travelling. */}
          <MoodCheckIn
            days={mood.days}
            today={mood.today}
            savingDay={mood.savingDay}
            onPick={mood.post}
          />

          {/* Framed like a kanban column, and tinted like one: a stack of cards
            read one after the other is the same object on both screens, and the
            tint is what tells the eye where the stack stops. */}
          {!home.isLoading && (
            <div className="rounded-xl border border-slate-300 bg-slate-100">
              <header className="flex items-center justify-between gap-2 px-3 pt-3 pb-2">
                <h2 className="text-sm font-medium text-slate-700">Quoi de neuf</h2>
                <span className="text-xs tabular-nums text-slate-400">
                  {home.updates.length}
                </span>
              </header>

              {home.updates.length === 0 ? (
                <p className="px-1 py-6 text-center text-xs text-slate-400">
                  Aucune nouvelle publiée sur vos projets
                </p>
              ) : (
                <div className="flex flex-col gap-2 px-2 pb-2">
                  {home.updates.map((entry) => (
                    <UpdateFeedItem
                      key={entry.item.project.id}
                      entry={entry}
                      now={now}
                      // Opened on its thread: the message one just read is what
                      // one is going there for.
                      onOpen={(projectId) => panel.open(projectId, "updates")}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </aside>
      </div>

      {panel.openedMission && (
        <ProjectPanel
          key={`${panel.openedMission}:${panel.openTab ?? ""}`}
          projectId={panel.openedMission}
          tab={panel.openTab}
          onClose={panel.close}
          // A phase or an urgency changed in the panel must read the same on
          // the card behind it.
          onMissionChanged={home.refresh}
          onOpenMission={(projectId) => panel.open(projectId)}
        />
      )}
    </PageLayout>
  );
}
