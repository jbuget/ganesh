"use client";

import Link from "next/link";
import { useMemo } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { AgendaItemCard } from "@/components/molecules/AgendaItemCard";
import { PageLayout } from "@/components/organisms/PageLayout";
import { useTeammates } from "@/lib/api/queries";
import { plural } from "@/lib/plurals";
import { useMayWrite } from "@/lib/use-may-write";
import { useReviewAgenda } from "@/lib/use-review-agenda";

/**
 * What the next revue has to discuss.
 *
 * The question this screen answers is the one a backlog review opens on and
 * has never had an answer to: which projects carry our intention of the
 * moment. It is not computed — nothing knows that but the people — so it is
 * collected: somebody says it out loud on the thread, marks it, and it lands
 * here until the meeting reads it.
 *
 * A project's lines are gathered under its name rather than read as one flat
 * chronology: read flat, the same project is picked up and dropped three
 * times over, and the meeting opens its thread three times.
 */
export function ReviewAgendaPage() {
  const { chapters, waiting, clear } = useReviewAgenda();
  const mayWrite = useMayWrite();
  const { teammates } = useTeammates();
  // Freezes the reference time for the whole screen: every « il y a trois
  // jours » on it must be counted from the same instant.
  const now = useMemo(() => new Date(), []);
  // Composée d'un seul tenant : une phrase française découpée en morceaux de
  // JSX s'accorde de travers sans que rien ne le voie.
  const summary =
    `${waiting} ${plural(waiting, "mise")} à jour à discuter, ` +
    `sur ${chapters?.length ?? 0} ${plural(chapters?.length ?? 0, "projet")}.`;

  return (
    <PageLayout
      header={
        <PageHeader
          title="À discuter"
          subtitle="Ce que la prochaine revue doit lire, du plus ancien au plus récent."
        />
      }
    >
      {/* Both branches read « chapters » once it is there: while it is being
          loaded neither is met, and nothing is drawn. An « aucune » shown for
          a moment and taken back would announce an empty revue to somebody
          who came to prepare one. */}
      {chapters?.length === 0 && (
        <p className="text-sm text-slate-500">
          Rien n&apos;attend d&apos;être discuté. Une mise à jour se signale depuis
          l&apos;onglet « Mises à jour » d&apos;un projet.
        </p>
      )}

      {chapters !== null && chapters.length > 0 && (
        <div className="space-y-6">
          {/* Composée d'un seul tenant : une phrase française découpée en
              morceaux de JSX s'accorde de travers sans que rien ne le voie. */}
          <p className="text-sm text-slate-500">{summary}</p>

          {chapters.map((chapter) => (
            <section key={chapter.projectId} className="space-y-2">
              {/* The heading names the project, so the lines under it do not. */}
              <h2 className="flex items-baseline gap-2 border-b border-slate-300 pb-1">
                <Link
                  href={`/projects/${chapter.projectId}`}
                  className="cursor-pointer text-sm font-medium text-slate-900 hover:underline"
                >
                  {chapter.label}
                </Link>
                <span className="text-xs text-slate-500">
                  {`${chapter.items.length} ${plural(chapter.items.length, "mise")} à jour`}
                </span>
              </h2>

              {chapter.items.map((item) => (
                <AgendaItemCard
                  key={item.update_id}
                  item={item}
                  now={now}
                  people={teammates}
                  onClear={
                    mayWrite
                      ? () => clear(chapter.projectId, item.update_id)
                      : undefined
                  }
                />
              ))}
            </section>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
