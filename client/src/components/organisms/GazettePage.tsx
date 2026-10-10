"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";

import { DigestChapeau } from "@/components/atoms/DigestChapeau";

import { DigestVersionPicker } from "@/components/atoms/DigestVersionPicker";
import { PageHeader } from "@/components/atoms/PageHeader";
import { RegenerateDigestDialog } from "@/components/atoms/RegenerateDigestDialog";
import { DigestHighlights } from "@/components/molecules/DigestHighlights";
import { DigestChapters } from "@/components/molecules/DigestChapters";
import { DigestTally } from "@/components/molecules/DigestTally";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Button } from "@/components/ui/button";
import { formatMonth } from "@/lib/dates";
import { formatGeneratedAt, isQuietMonth, projectLabels } from "@/lib/gazette";
import { useGazette } from "@/lib/use-gazette";

/**
 * La Gazette: one month of the register, read back.
 *
 * The register records everything as it happens, and until now it was only
 * ever read one project at a time, by whoever already knew what they were
 * looking for. This is the same register read across, month by month.
 *
 * Two things are told apart on purpose, and the whole screen rests on it: the
 * facts come from the register and are counted by the application, while the
 * paragraph at the top was written by a model over those facts and carries no
 * figure. Anyone may ask for a digest, and asking again never rewrites one —
 * it writes the next version beside it.
 */
export function GazettePage() {
  const gazette = useGazette();
  const [isConfirming, setConfirming] = useState(false);
  const monthName = formatMonth(gazette.cursor.year, gazette.cursor.month);
  const digest = gazette.digest;

  const header = (
    <PageHeader
      title="La Gazette"
      subtitle="Ce que le mois a changé, projet par projet."
      actions={
        <>
          {digest && digest.version !== null && (
            <DigestVersionPicker
              versions={digest.versions}
              current={digest.version}
              onOpen={gazette.openVersion}
            />
          )}
          <Button
            className="cursor-pointer"
            disabled={gazette.isGenerating || !digest}
            onClick={() => {
              // Asking for a month that has never been read needs no
              // confirmation: there is nothing yet to think twice about.
              if (digest?.is_generated) setConfirming(true);
              else void gazette.generateDigest();
            }}
          >
            {gazette.isGenerating
              ? "Génération…"
              : digest?.is_generated
                ? "Regénérer"
                : "Générer le digest"}
          </Button>
        </>
      }
    />
  );

  if (!digest) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">
          {gazette.isLoading ? "Chargement du digest…" : "Digest indisponible."}
        </p>
      </PageLayout>
    );
  }

  return (
    <PageLayout header={header}>
      <div className="flex flex-col gap-6 pb-4">
        {/* Nothing but the month on this line, centred on it, as on the entry
            grid: the actions sit in the header, where every screen carries
            them. */}
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="icon"
            className="cursor-pointer"
            aria-label="Mois précédent"
            onClick={gazette.goToPreviousMonth}
          >
            <ChevronLeft />
          </Button>
          <h2 className="min-w-48 text-center text-lg font-semibold capitalize">
            {monthName}
          </h2>
          <Button
            variant="outline"
            size="icon"
            className="cursor-pointer"
            aria-label="Mois suivant"
            onClick={gazette.goToNextMonth}
          >
            <ChevronRight />
          </Button>
        </div>

        {digest.is_generated ? (
          <p className="text-center text-xs text-slate-500">
            Version {digest.version}, demandée par {digest.requested_by} le{" "}
            {digest.generated_at && formatGeneratedAt(digest.generated_at)}
          </p>
        ) : (
          /* A month nobody has asked for is readable all the same: its facts
             come from a register everyone already has open. What it does not
             carry is a chapeau, a date and a name — and the promise that it
             will still say this tomorrow. */
          <p className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-center text-sm text-slate-600">
            Ce mois n&apos;a pas encore de digest. Vous lisez le journal tel qu&apos;il
            est en ce moment ; il bougera encore.
          </p>
        )}

        {digest.prose && digest.prose_model && (
          <DigestChapeau
            prose={digest.prose}
            model={digest.prose_model}
            labels={projectLabels(digest)}
          />
        )}

        <DigestTally tally={digest.tally} />

        {isQuietMonth(digest) ? (
          <p className="py-8 text-center text-sm text-slate-500">
            Rien n&apos;a été enregistré ce mois-ci.
          </p>
        ) : (
          <>
            {digest.highlights.length > 0 && (
              <DigestHighlights highlights={digest.highlights} />
            )}

            {digest.chapters.length > 0 && (
              <section>
                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Le mois, projet par projet
                </h3>
                <DigestChapters chapters={digest.chapters} />
              </section>
            )}
          </>
        )}
      </div>

      <RegenerateDigestDialog
        open={isConfirming}
        onOpenChange={setConfirming}
        month={monthName}
        onConfirm={() => {
          setConfirming(false);
          void gazette.generateDigest();
        }}
      />
    </PageLayout>
  );
}
