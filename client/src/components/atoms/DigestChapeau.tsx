import { Sparkles } from "lucide-react";

interface DigestChapeauProps {
  /** What the model wrote. Nothing to draw when it wrote nothing that held. */
  prose: string;
  /** Which model wrote it: a reader weighs the paragraph once they know. */
  model: string;
}

/**
 * The one paragraph of a digest a machine wrote.
 *
 * Told apart from the facts under it, and named as machine-written, because a
 * reader weighs the two differently — and should. It carries no figure: the
 * counting is the register's, and it is printed beside this, not in it.
 */
export function DigestChapeau({ prose, model }: DigestChapeauProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-sm leading-relaxed text-slate-800">{prose}</p>
      <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
        <Sparkles className="size-3.5 shrink-0" aria-hidden />
        Texte rédigé par {model} à partir des faits ci-dessous. Les chiffres, eux,
        viennent du journal.
      </p>
    </section>
  );
}
