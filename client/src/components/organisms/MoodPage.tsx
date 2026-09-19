"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { MoodsTable } from "@/components/organisms/MoodsTable";
import { PageLayout } from "@/components/organisms/PageLayout";
import { useTeamMoodScreen } from "@/lib/use-team-mood";

/**
 * The team's morale over the last fortnight.
 *
 * Everyone reads it, and that is assumed: it is a mirror the team holds up to
 * itself, not a measure taken of it. Which is also why nothing is answered
 * from here — one posts one's own day from the home screen, and a screen that
 * did both would put the answer under the eyes of what it is about.
 *
 * Working days alone: four empty lines of weekend over a fortnight would say
 * nothing but that nobody works on Sundays.
 */
export function MoodPage() {
  const screen = useTeamMoodScreen();

  const header = (
    <PageHeader
      title="Moral de l'équipe"
      subtitle="Les 14 derniers jours, jours ouvrés seulement. Chacun répond depuis son Accueil."
    />
  );

  return (
    <PageLayout header={header}>
      {screen.isLoading ? (
        <p className="text-sm text-slate-500">Chargement…</p>
      ) : screen.days.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
          Aucun jour à afficher sur la quinzaine.
        </p>
      ) : (
        <MoodsTable
          days={screen.days}
          headcount={screen.headcount}
          today={screen.today}
        />
      )}
    </PageLayout>
  );
}
