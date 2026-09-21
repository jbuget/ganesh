"use client";

import { MetricTile } from "@/components/atoms/MetricTile";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RangeSelect } from "@/components/atoms/RangeSelect";
import { CoverageHeadline } from "@/components/molecules/CoverageHeadline";
import { ShareBreakdown } from "@/components/molecules/ShareBreakdown";
import { PageLayout } from "@/components/organisms/PageLayout";
import { SurfaceUsageTable } from "@/components/organisms/SurfaceUsageTable";
import {
  NOTHING,
  categoryRows,
  formatDelay,
  formatShare,
  kindRows,
  missionRows,
  phaseRows,
  summarise,
} from "@/lib/statistics";
import { useStatisticsScreen } from "@/lib/use-statistics-screen";

/**
 * The dashboard: is what we build actually used, and is it worth using?
 *
 * The blocks are ordered as the question is answered. Coverage leads, because
 * nothing below it means anything if the data is full of holes. Reliability
 * comes next, then adoption — of the team, then of each function of the
 * product — then what the data teaches: that last floor is the only one that
 * proves the point, and it is only readable once the ones above hold.
 */
export function StatsPage() {
  const { range, setRange, statistics, isLoading, alerts } = useStatisticsScreen();

  const header = (
    <PageHeader
      title="Statistiques"
      subtitle={
        statistics
          ? summarise(statistics.period)
          : "Ce que vaut cet outil : sa couverture, sa fiabilité, son usage."
      }
      actions={<RangeSelect value={range} onChange={setRange} />}
    />
  );

  if (!statistics) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">
          {isLoading ? "Chargement des statistiques…" : "Statistiques indisponibles."}
        </p>
      </PageLayout>
    );
  }

  const {
    coverage,
    freshness,
    month_validation,
    adoption,
    surfaces,
    steering,
    registry,
  } = statistics;

  return (
    <PageLayout header={header}>
      <div className="mx-auto flex max-w-4xl flex-col gap-8 pb-4">
        <CoverageHeadline coverage={coverage} medianDelay={freshness.median_delay} />

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">Fiabilité</h2>
          <p className="mb-3 text-sm text-slate-500">
            Peut-on se fier à ces chiffres ? Une couverture élevée mais reconstituée de
            mémoire ne vaut rien.
          </p>
          <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricTile
              label="Délai médian de saisie"
              value={formatDelay(freshness.median_delay)}
              hint={
                freshness.entries === 0
                  ? "aucune saisie écrite sur la période"
                  : `sur ${freshness.entries} saisie${freshness.entries > 1 ? "s" : ""} écrite${freshness.entries > 1 ? "s" : ""} sur la période`
              }
            />
            <MetricTile
              label="Saisi au fil de l'eau"
              value={formatShare(freshness.day_to_day_share)}
              hint="déclaré dans les 2 jours"
            />
            <MetricTile
              label="Rattrapé tardivement"
              value={formatShare(freshness.late_share)}
              hint="déclaré plus de 15 jours après"
              tone={alerts.lateCatchUp ? "warning" : "plain"}
            />
            <MetricTile
              label="Mois validés"
              value={formatShare(month_validation.rate)}
              hint={
                month_validation.due === 0
                  ? "aucun mois échu sur la période"
                  : `${month_validation.validated} sur ${month_validation.due} attendus`
              }
            />
          </dl>
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">Adoption</h2>
          <p className="mb-3 text-sm text-slate-500">
            L&apos;équipe s&apos;en sert-elle d&apos;elle-même ?
          </p>
          <dl className="grid gap-3 sm:grid-cols-3">
            <MetricTile
              label="Part de l'équipe ayant saisi"
              value={formatShare(adoption.rate)}
              hint={`${adoption.contributors} sur ${adoption.expected_contributors} collaborateurs`}
            />
            <MetricTile
              label="Sans aucune saisie"
              value={String(adoption.idle.length)}
              hint={
                adoption.idle.length === 0
                  ? "toute l'équipe a déclaré"
                  : adoption.idle.map((teammate) => teammate.display_name).join(", ")
              }
              tone={alerts.idleTeammates ? "warning" : "plain"}
            />
          </dl>
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">
            Fonctions utilisées
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            Qu&apos;est-ce qui sert, et qu&apos;est-ce qui ne sert plus ? Le bloc
            au-dessus compte les personnes, celui-ci compte les fonctions.
          </p>
          <SurfaceUsageTable usage={surfaces} />
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">
            Valeur de pilotage
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            Que nous apprend la donnée ? C&apos;est ce que les saisies ont été capturées
            pour dire.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <ShareBreakdown title="Projet ou hors projet" rows={kindRows(steering)} />
            <ShareBreakdown title="Temps par phase" rows={phaseRows(steering)} />
            <ShareBreakdown
              title="Temps par axe stratégique"
              rows={categoryRows(steering)}
            />
            <ShareBreakdown
              title="Projets les plus consommateurs"
              rows={missionRows(steering)}
            />
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">
            Santé du référentiel
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            Le référentiel de projets reflète-t-il le travail réel ?
          </p>
          <dl className="grid gap-3 sm:grid-cols-3">
            <MetricTile
              label="Projets actifs"
              value={String(registry.active_missions)}
              hint={
                registry.usage_rate === null || registry.usage_rate === undefined
                  ? NOTHING
                  : `${formatShare(registry.usage_rate)} ont reçu du temps`
              }
            />
            <MetricTile
              label="Sans aucun temps"
              value={String(registry.missions_without_time)}
              hint="projets actifs que personne n'a servis"
            />
            <MetricTile
              label="Projets créés"
              value={String(registry.created)}
              hint="ajoutées au référentiel sur la période"
            />
          </dl>
        </section>
      </div>
    </PageLayout>
  );
}
