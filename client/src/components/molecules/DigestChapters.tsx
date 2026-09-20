import { DigestFactLine } from "@/components/atoms/DigestFactLine";
import type { ChapterResponse, MovementKind } from "@/lib/api/generated/model";
import { formatShortDate } from "@/lib/dates";
import { chapterTitle, movementPredicate } from "@/lib/gazette";

interface DigestChaptersProps {
  chapters: ChapterResponse[];
}

/**
 * The tint of each kind of movement.
 *
 * It follows what the fact means, not what it is about: a mise en service is
 * green wherever it appears, a step backwards amber. Anything that merely
 * happened stays slate — colour marks what deserves marking, and a list where
 * every line is coloured marks nothing.
 */
const DOTS: Record<MovementKind, string> = {
  project_created: "bg-sky-500",
  project_archived: "bg-slate-400",
  project_revived: "bg-sky-500",
  phase_advanced: "bg-slate-300",
  phase_stepped_back: "bg-amber-500",
  went_live: "bg-emerald-500",
  news_posted: "bg-slate-300",
  teammate_joined: "bg-violet-500",
  teammate_returned: "bg-violet-500",
  teammate_left: "bg-slate-400",
};

/**
 * The month, mission by mission, each one day after day.
 *
 * Gathered rather than flat: a single list of everything that happened reads
 * as the log it came from, where the same mission is picked up and dropped
 * ten times over. Under its own heading, a mission's month reads as a story —
 * and its work packages are told inside it, because that is where their month
 * belongs.
 *
 * The heading names the mission, so the lines under it do not: « est passé en
 * exploitation », not « WAATcher est passé en exploitation » under a heading
 * already reading « WAATcher ».
 */
export function DigestChapters({ chapters }: DigestChaptersProps) {
  return (
    <div className="flex flex-col gap-4">
      {chapters.map((chapter) => (
        <section key={chapter.project_id ?? "team"}>
          <h4 className="text-sm font-medium text-slate-900">
            {chapterTitle(chapter)}
          </h4>
          <Lines chapter={chapter} />

          {chapter.packages.map((packageChapter) => (
            // Indented and named again: a package's month is its own, told
            // inside its project rather than merged into it.
            <div
              key={packageChapter.project_id}
              className="mt-1 border-l border-slate-200 pl-3"
            >
              <h5 className="text-sm text-slate-600">{chapterTitle(packageChapter)}</h5>
              <Lines chapter={packageChapter} />
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}

function Lines({ chapter }: { chapter: ChapterResponse }) {
  if (chapter.movements.length === 0) return null;

  return (
    <ul>
      {chapter.movements.map((movement, rank) => (
        <DigestFactLine
          key={`${movement.at}-${movement.kind}-${rank}`}
          sentence={movementPredicate(movement)}
          dot={DOTS[movement.kind] ?? "bg-slate-300"}
          when={formatShortDate(movement.at)}
        />
      ))}
    </ul>
  );
}
