"use client";

import { useState } from "react";

import { DigestFactLine } from "@/components/atoms/DigestFactLine";
import type { HighlightResponse, Tone } from "@/lib/api/generated/model";
import { TONE_TITLES, highlightSentence } from "@/lib/gazette";

interface DigestHighlightsProps {
  highlights: HighlightResponse[];
}

/** Green for what was achieved, amber for what is worth going to look at. */
const DOTS: Record<Tone, string> = {
  notable: "bg-emerald-500",
  attention: "bg-amber-500",
};

/**
 * Past this, a list stops being read and starts being scrolled past.
 *
 * One tidying-up of the reference list archives a dozen projects at once, and
 * a dozen identical worries bury the one fact of the month that mattered.
 */
const SHOWN_UNFOLDED = 5;

/**
 * What a month is worth reading twice.
 *
 * Each of these is a rule the domain applied and a test pins down — never a
 * model's reading of the month. A model asked to underline what stands out
 * underlines something even when nothing does.
 *
 * Every line is about a project, and none about a person: a digest that named
 * who was late would be read as a list of names, whatever else it said.
 *
 * A long list folds, as the roadmap's does and for the same reason: what is
 * folded away is counted in plain sight beside the title, never dropped. The
 * count is itself a fact about the month.
 *
 * The two stack rather than sitting side by side: there are structurally more
 * worries than achievements — a date once missed is missed again every month
 * until it is met — and two columns would leave the left one half empty while
 * cramping the right, saying the two weigh the same. Stacked, what went well
 * is read first and the long list runs the full width.
 */
export function DigestHighlights({ highlights }: DigestHighlightsProps) {
  const [unfolded, setUnfolded] = useState<Tone[]>([]);
  const tones: Tone[] = ["notable", "attention"];

  return (
    <div className="flex flex-col gap-4">
      {tones.map((tone) => {
        const ofThisTone = highlights.filter((highlight) => highlight.tone === tone);
        if (ofThisTone.length === 0) return null;

        const isUnfolded = unfolded.includes(tone);
        const hidden = ofThisTone.length - SHOWN_UNFOLDED;
        const shown = isUnfolded ? ofThisTone : ofThisTone.slice(0, SHOWN_UNFOLDED);

        return (
          <section key={tone}>
            <h3 className="mb-1 text-sm font-semibold text-slate-900">
              {TONE_TITLES[tone]}{" "}
              <span className="font-normal text-slate-500 tabular-nums">
                ({ofThisTone.length})
              </span>
            </h3>
            <ul>
              {shown.map((highlight) => (
                <DigestFactLine
                  key={`${highlight.kind}-${highlight.project_id}`}
                  sentence={highlightSentence(highlight)}
                  dot={DOTS[tone]}
                />
              ))}
            </ul>

            {hidden > 0 && (
              <button
                type="button"
                className="mt-1 cursor-pointer text-xs text-sky-700 underline-offset-2 hover:underline"
                onClick={() =>
                  setUnfolded((tones) =>
                    isUnfolded ? tones.filter((it) => it !== tone) : [...tones, tone],
                  )
                }
              >
                {isUnfolded ? "Replier" : `Voir les ${hidden} autres`}
              </button>
            )}
          </section>
        );
      })}
    </div>
  );
}
