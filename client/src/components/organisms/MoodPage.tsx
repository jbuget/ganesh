"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { MoodBubbleChart } from "@/components/molecules/MoodBubbleChart";
import { MoodsTable } from "@/components/organisms/MoodsTable";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTeamMoodScreen } from "@/lib/use-team-mood";

/**
 * The team's morale over the last fortnight.
 *
 * Everyone reads it, and that is assumed: it is a mirror the team holds up to
 * itself, not a measure taken of it. Which is also why nothing is answered
 * from here — a screen that did both would put the answer under the eyes of
 * what it is about. One posts one's own day from the home screen, or from the
 * reminder of the late afternoon, which keeps away from this screen for that
 * very reason.
 *
 * Two tabs over the same fortnight, and the order between them is the reading:
 * « Récap » names who said what, « Tendances » sums it up. One starts on the
 * people and steps back to the shape, never the other way round — a curve read
 * before the days it is made of is a figure one trusts without having seen it.
 *
 * Not « Journal »: a mission's tabs already give that name to its audit trail,
 * and one word must not name two different things.
 *
 * Working days alone: four empty lines of weekend over a fortnight would say
 * nothing but that nobody works on Sundays.
 */
export function MoodPage() {
  const screen = useTeamMoodScreen();

  const header = (
    <PageHeader
      title="Moral de l'équipe"
      subtitle="Comment va l'équipe, sur les quatorze derniers jours ouvrés."
    />
  );

  if (screen.isLoading) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">Chargement…</p>
      </PageLayout>
    );
  }

  if (screen.days.length === 0) {
    return (
      <PageLayout header={header}>
        <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
          Aucun jour à afficher sur la quinzaine.
        </p>
      </PageLayout>
    );
  }

  return (
    <PageLayout header={header}>
      <Tabs defaultValue="recap" className="flex flex-col gap-4">
        <TabsList className="w-fit">
          <TabsTrigger value="recap">Récap</TabsTrigger>
          <TabsTrigger value="trends">Tendances</TabsTrigger>
        </TabsList>

        <TabsContent value="recap">
          <MoodsTable
            days={screen.days}
            headcount={screen.headcount}
            today={screen.today}
          />
        </TabsContent>

        <TabsContent value="trends">
          <MoodBubbleChart days={screen.days} />
        </TabsContent>
      </Tabs>
    </PageLayout>
  );
}
