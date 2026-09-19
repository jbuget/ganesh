/**
 * What the three textures mean.
 *
 * Not decoration: the whole screen rests on telling a fact from a
 * supposition, and a reader who has not been told which is which will read
 * both as a commitment.
 */
export function RoadmapLegend() {
  return (
    <ul className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-slate-500">
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="h-2.5 w-6 rounded-sm bg-slate-400" />
        Vécu
      </li>
      <li className="flex items-center gap-1.5">
        <span
          aria-hidden
          className="h-2.5 w-6 rounded-sm bg-slate-400 [background-image:repeating-linear-gradient(135deg,transparent_0_3px,rgba(255,255,255,0.65)_3px_6px)]"
        />
        Projeté
      </li>
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="h-px w-6 bg-emerald-500" />
        En exploitation
      </li>
      <li className="flex items-center gap-1.5">
        <span
          aria-hidden
          className="size-2.5 rotate-45 border border-slate-600 bg-white"
        />
        Date annoncée
      </li>
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="h-px w-6 bg-red-500" />
        Glissement
      </li>
    </ul>
  );
}
