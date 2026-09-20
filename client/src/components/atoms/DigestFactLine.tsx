interface DigestFactLineProps {
  /** The fact, already said in French. */
  sentence: string;
  /** The colour of the mark. Shape stays the same: only the tint moves. */
  dot: string;
  /** When it happened, when the line is one of a chronology. */
  when?: string;
}

/**
 * One fact of the month: a coloured mark, then a sentence in ordinary text.
 *
 * The same grammar as phases, priorities and axes across the application —
 * colour marks, it never fills.
 */
export function DigestFactLine({ sentence, dot, when }: DigestFactLineProps) {
  return (
    <li className="flex items-baseline gap-2.5 py-1.5 text-sm">
      <span className={`mt-1.5 size-2 shrink-0 rounded-full ${dot}`} aria-hidden />
      <span className="min-w-0 flex-1 text-slate-800">{sentence}</span>
      {when && (
        <span className="shrink-0 text-xs tabular-nums text-slate-400">{when}</span>
      )}
    </li>
  );
}
