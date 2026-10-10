"use client";

import { MetricTile } from "@/components/atoms/MetricTile";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RangeSelect } from "@/components/atoms/RangeSelect";
import { ActivityMosaic } from "@/components/molecules/ActivityMosaic";
import { CoverageHeadline } from "@/components/molecules/CoverageHeadline";
import { IntakeMovements } from "@/components/molecules/IntakeMovements";
import { NotificationReadRates } from "@/components/molecules/NotificationReadRates";
import { ShareBreakdown } from "@/components/molecules/ShareBreakdown";
import { TradeSplit } from "@/components/molecules/TradeSplit";
import { PageLayout } from "@/components/organisms/PageLayout";
import { SurfaceUsageTable } from "@/components/organisms/SurfaceUsageTable";
import {
  NOTHING,
  categoryRows,
  formatDelay,
  formatShare,
  formatWait,
  kindRows,
  missionRows,
  phaseRows,
  summarise,
} from "@/lib/statistics";
import { teamLabel } from "@/lib/teams";
import { useStatisticsScreen } from "@/lib/use-statistics-screen";

/**
 * The dashboard: is what we build actually used, and is it worth using?
 *
 * The blocks are ordered as the question is answered. Coverage leads, because
 * nothing below it means anything if the data is full of holes. Reliability
 * comes next, then adoption — of the team, of who has been let in, then of
 * each function of the product and of the recueil — then what the data
 * teaches: that floor is the only one that proves the point, and it is only
 * readable once the ones above hold. The reference list closes the page, since
 * it says whether the data could be declared at all.
 *
 * Three diagrams, no more: the coverage curve under the lead figure, the
 * movements of the recueil, and the bar splitting the time by trade. Each one
 * is there because a figure alone hides what it shows; everything else stays a
 * figure, a bar or a table.
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
    accounts,
    surfaces,
    steering,
    registry,
    intake,
    stewardship,
    thread,
    notification_reading: notifications,
  } = statistics;

  return (
    <PageLayout header={header}>
      <div className="mx-auto flex max-w-4xl flex-col gap-8 pb-4">
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">Activité</h2>
          <p className="mb-3 text-sm text-slate-500">
            Le produit est-il habité tous les jours, ou par à-coups ? Chaque case est un
            jour de l&apos;année écoulée, d&apos;autant plus foncée que le journal y
            compte de gestes. Elle ne suit pas la période choisie.
          </p>
          <ActivityMosaic days={statistics.activity} />
        </section>

        <CoverageHeadline
          coverage={coverage}
          trend={statistics.coverage_trend}
          medianDelay={freshness.median_delay}
        />

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
              hint={`${adoption.contributors} sur ${adoption.expected_contributors} collaborateurs · équipe ${teamLabel(coverage.team)}`}
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
            Comptes et accès
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            Qui est entré, et jusqu&apos;où ? Un compte qui n&apos;a pas de rôle
            n&apos;a accès qu&apos;à « Mes demandes ».
          </p>
          <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricTile
              label="Invités en attente d'un rôle"
              value={String(accounts.guests)}
              hint="ne voient que « Mes demandes »"
            />
            <MetricTile
              label="Jamais connectés"
              value={String(accounts.never_signed_in)}
              hint="comptes ouverts d'avance, jamais utilisés"
            />
            <MetricTile
              label="Reçoivent le récapitulatif"
              value={formatShare(accounts.reminder_rate)}
              hint={`${accounts.reminders_daily} chaque jour · ${accounts.reminders_weekly} chaque semaine · ${accounts.reminders_never} jamais`}
            />
            <MetricTile
              label="Rôles de l'équipe"
              value={String(accounts.teammates + accounts.managers + accounts.admins)}
              hint={`${accounts.teammates} équipier${accounts.teammates > 1 ? "s" : ""} · ${accounts.managers} responsable${accounts.managers > 1 ? "s" : ""} · ${accounts.admins} administrateur${accounts.admins > 1 ? "s" : ""}`}
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
            Recueil de besoins
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            Ce que l&apos;entreprise demande, et ce qu&apos;on en fait. Un besoin
            n&apos;est pas un projet : il se lit à part.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <IntakeMovements intake={intake} />
            <dl className="grid content-start gap-3">
              <MetricTile
                label="En attente d'une réponse"
                value={String(intake.waiting)}
                hint={
                  intake.waiting === 0
                    ? "aucun besoin en attente"
                    : `le plus ancien attend depuis ${formatWait(intake.oldest_wait_days)}`
                }
              />
            </dl>
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">Vie des projets</h2>
          <p className="mb-3 text-sm text-slate-500">
            Quelqu&apos;un répond-il de chaque projet, et en donne-t-on des nouvelles ?
          </p>
          <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricTile
              label="Sans référent technique"
              value={String(stewardship.without_tech_lead)}
              hint={`sur ${stewardship.active_projects} projets actifs · le prochain bug n'arriverait à personne`}
              tone={alerts.withoutTechLead ? "warning" : "plain"}
            />
            <MetricTile
              label="Sans référent projet"
              value={String(stewardship.without_lead)}
              hint={`sur ${stewardship.active_projects} projets actifs`}
            />
            <MetricTile
              label="Suivis sans nouvelles"
              value={String(thread.silent)}
              hint={
                thread.followed === 0
                  ? "aucun projet suivi"
                  : `sur ${thread.followed} projets suivis · rien depuis plus de 14 jours`
              }
              tone={alerts.silentFollowed ? "warning" : "plain"}
            />
            <MetricTile
              label="Actualités qui ont reçu une réponse"
              value={formatShare(thread.answer_rate)}
              hint={
                thread.posted === 0
                  ? "aucune actualité publiée sur la période"
                  : `${thread.answered} sur ${thread.posted} · réponse ou réaction d'un autre que l'auteur`
              }
            />
          </dl>
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-900">
            Notifications lues
          </h2>
          <p className="mb-3 text-sm text-slate-500">
            Ce que le produit dit est-il entendu ? Une notification jamais ouverte est
            un message qui ne sert à personne.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <NotificationReadRates reading={notifications} />
            <dl className="grid content-start gap-3">
              <MetricTile
                label="Notifications ouvertes"
                value={formatShare(notifications.read_rate)}
                hint={
                  notifications.delivered === 0
                    ? "aucune notification envoyée sur la période"
                    : `${notifications.read} sur ${notifications.delivered} envoyées sur la période`
                }
              />
              <MetricTile
                label="En attente de lecture"
                value={String(notifications.unread)}
                hint="à ce jour, quelle que soit leur date"
              />
              <MetricTile
                label="Laissées sans lecture"
                value={String(notifications.ignored)}
                hint="en attente depuis plus de 14 jours"
                tone={notifications.ignored > 0 ? "warning" : "plain"}
              />
            </dl>
          </div>
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
            <TradeSplit steering={steering} />
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
          <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
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
              hint="ajoutés au référentiel sur la période"
            />
            <MetricTile
              label="Sans activité"
              value={String(registry.without_activity)}
              hint="aucune saisie possible tant qu'un métier n'est pas ajouté"
              tone={alerts.withoutActivity ? "warning" : "plain"}
            />
            <MetricTile
              label="Budget incomplet"
              value={String(registry.unbudgeted)}
              hint="un métier sans estimation : le projet n'a pas d'estimation"
            />
            <MetricTile
              label="Projets suivis"
              value={String(registry.followed)}
              hint="ceux que l'équipe garde à l'œil"
            />
            <MetricTile
              label="Publiés au catalogue"
              value={String(registry.published)}
              hint="visibles sur waat.tools"
            />
          </dl>
        </section>
      </div>
    </PageLayout>
  );
}
