import { emphasiseProjects, paragraphsOf } from "@/lib/gazette";

interface EmphasisedParagraphsProps {
  /** What the model wrote, paragraphs apart by a blank line. */
  text: string;
  /** The projects and people it may name, to be set in bold. */
  names: string[];
}

/**
 * A text a model wrote, in paragraphs, with every name set in the same weight.
 *
 * The emphasis is put on here, at the last moment, by matching names the
 * digest and the reference list already carry — the model is never asked for
 * markup, and a name it did not write as it is carried is left plain rather
 * than guessed at.
 */
export function EmphasisedParagraphs({ text, names }: EmphasisedParagraphsProps) {
  return (
    <div className="flex flex-col gap-3 text-sm leading-relaxed text-slate-800">
      {paragraphsOf(text).map((paragraph, index) => (
        <p key={index}>
          {emphasiseProjects(paragraph, names).map((segment, rank) =>
            segment.isName ? (
              <strong key={rank} className="font-semibold text-slate-900">
                {segment.text}
              </strong>
            ) : (
              <span key={rank}>{segment.text}</span>
            ),
          )}
        </p>
      ))}
    </div>
  );
}
