"use client";

import { DigestFactLine } from "@/components/atoms/DigestFactLine";
import { DigestNarrative } from "@/components/molecules/DigestNarrative";
import { DigestTally } from "@/components/molecules/DigestTally";
import { formatMonth } from "@/lib/dates";
import { formatGeneratedAt, missionName } from "@/lib/gazette";
import { useSharedDigest } from "@/lib/api/queries";

interface SharedGazettePageProps {
  token: string;
}

/**
 * One version of a digest, for somebody outside the company.
 *
 * Bare on purpose: no sidebar, no search, no button, nothing that suggests
 * there is an application behind it to sign in to or act in. It reads what
 * `PublicDigest` hands over — the narrative and the figures — and a link that
 * was closed says only that it opens nothing, as one that never existed does.
 */
export function SharedGazettePage({ token }: SharedGazettePageProps) {
  const { digest, isLoading, isError } = useSharedDigest(token);

  if (isLoading) {
    return <Frame>Chargement…</Frame>;
  }
  if (isError || !digest) {
    return (
      <Frame>
        <p className="text-sm text-slate-600">
          Ce lien n&apos;ouvre rien, ou il n&apos;est plus valable.
        </p>
      </Frame>
    );
  }

  const [year, month] = digest.month.split("-").map(Number);
  return (
    <Frame>
      <header className="mb-6">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Ganesh — WAAT
        </p>
        <h1 className="mt-1 text-2xl font-semibold capitalize text-slate-900">
          La Gazette · {formatMonth(year, month)}
        </h1>
        <p className="mt-1 text-xs text-slate-500">
          Version {digest.version}, du {formatGeneratedAt(digest.generated_at)}
        </p>
      </header>

      <div className="flex flex-col gap-6">
        {digest.prose_model && (digest.prose || digest.spotlights.length > 0) && (
          <DigestNarrative
            prose={digest.prose}
            spotlights={digest.spotlights}
            model={digest.prose_model}
            names={digest.names}
          />
        )}

        <DigestTally tally={digest.tally} />

        {digest.went_live.length > 0 && (
          <section>
            <h2 className="mb-1 text-sm font-semibold text-slate-900">
              Mis en service
            </h2>
            <ul>
              {digest.went_live.map((label) => (
                <DigestFactLine
                  key={label}
                  sentence={`${missionName(label)} est passé en exploitation`}
                  dot="bg-emerald-500"
                />
              ))}
            </ul>
          </section>
        )}
      </div>
    </Frame>
  );
}

function Frame({ children }: { children: React.ReactNode }) {
  return <main className="mx-auto max-w-3xl px-4 py-10">{children}</main>;
}
