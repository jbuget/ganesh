import { Circle } from "lucide-react";

interface WiringMarkProps {
  configured: boolean;
}

/**
 * Whether a service is wired: a coloured mark, then a label in ordinary text.
 *
 * The same grammar as the phase, the priority and the category — colour marks,
 * it does not fill. Filled means wired, hollow means not: the shape carries it
 * on its own for whoever cannot tell the two colours apart.
 */
export function WiringMark({ configured }: WiringMarkProps) {
  return (
    <span className="flex items-center gap-1.5 text-sm text-slate-700">
      <Circle
        aria-hidden
        className={
          configured
            ? "size-2.5 shrink-0 fill-emerald-500 text-emerald-500"
            : "size-2.5 shrink-0 text-slate-400"
        }
      />
      {configured ? "Câblé" : "Non câblé"}
    </span>
  );
}
