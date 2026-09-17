"use client";

import { MessageCircle } from "lucide-react";

import type { LastUpdateResponse } from "@/lib/api/generated/model";
import { apercuMarkdown } from "@/lib/apercu-markdown";
import { depuis } from "@/lib/dates-relatives";
import { useTooltipCurseur } from "@/lib/use-tooltip-curseur";

interface UpdatesCounterProps {
  nombre: number;
  /** La derniere mise a jour encore lisible, s'il en reste une. */
  derniere: LastUpdateResponse | null;
  /** Fige l'heure de reference : sans cela, serveur et client divergeraient. */
  maintenant: Date;
}

/**
 * Le fil de suivi d'une mission, en un nombre.
 *
 * Savoir qu'il y a trois messages ne dit pas s'il faut les lire : l'infobulle
 * donne le dernier, signe et date, et cela suffit le plus souvent a s'epargner
 * l'ouverture du panneau. C'est un apercu, pas une lecture — le markdown y est
 * depouille et le texte borne.
 *
 * Une mission sans mise a jour ne montre rien : dans un tableau, seul ce qui
 * se lit s'affiche.
 */
export function UpdatesCounter({ nombre, derniere, maintenant }: UpdatesCounterProps) {
  const { tooltip, suivre, quitter } = useTooltipCurseur({ riche: true });

  if (nombre === 0) return null;

  const apercu = derniere && (
    <>
      <span className="block font-medium">
        {derniere.author.display_name} · {depuis(derniere.publiee_le, maintenant)}
      </span>
      <span className="mt-1 block text-slate-300">
        {apercuMarkdown(derniere.texte)}
      </span>
    </>
  );

  return (
    <span
      aria-label={`${nombre} ${nombre > 1 ? "mises à jour" : "mise à jour"}`}
      onMouseMove={(event) => apercu && suivre(event, apercu)}
      onMouseLeave={quitter}
      className="inline-flex items-center gap-1 text-xs tabular-nums text-slate-500"
    >
      {nombre}
      <MessageCircle className="size-3.5 shrink-0" aria-hidden />
      {tooltip}
    </span>
  );
}
