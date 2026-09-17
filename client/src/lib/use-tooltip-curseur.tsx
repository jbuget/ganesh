"use client";

import {
  useLayoutEffect,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

/** Decalage de l'infobulle par rapport au curseur, pour ne pas le masquer. */
const OFFSET = { x: 14, y: 18 };

/** Ce qu'on laisse respirer entre la bulle et le bord de la fenetre. */
const MARGE = 8;

interface Etat {
  x: number;
  y: number;
  contenu: ReactNode;
}

/**
 * La bulle elle-meme, repliee dans la fenetre.
 *
 * Posee telle quelle au curseur, une bulle haute ou large sortirait de l'ecran
 * par le bas ou la droite — d'autant plus qu'elle ne se defile pas. On la
 * mesure donc avant peinture pour la ramener dans la fenetre : `useLayoutEffect`
 * s'execute entre le rendu et l'affichage, la correction ne se voit pas.
 */
function Bulle({
  x,
  y,
  riche,
  children,
}: Etat & { riche: boolean; children: ReactNode }) {
  const element = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ left: x + OFFSET.x, top: y + OFFSET.y });

  useLayoutEffect(() => {
    if (!element.current) return;
    const { width, height } = element.current.getBoundingClientRect();

    // A droite et en bas du curseur par defaut ; de l'autre cote s'il n'y a
    // plus la place, et cale contre le bord si elle n'y tient nulle part.
    const left =
      x + OFFSET.x + width > window.innerWidth - MARGE
        ? Math.max(MARGE, x - OFFSET.x - width)
        : x + OFFSET.x;
    const top =
      y + OFFSET.y + height > window.innerHeight - MARGE
        ? Math.max(MARGE, window.innerHeight - MARGE - height)
        : y + OFFSET.y;

    setPosition({ left, top });
  }, [x, y]);

  return (
    <div
      ref={element}
      role="tooltip"
      style={position}
      className={
        riche
          ? "pointer-events-none fixed z-50 max-w-md rounded-lg border border-slate-200 bg-white px-3 py-2.5 shadow-xl"
          : "pointer-events-none fixed z-50 rounded-md bg-slate-800 px-2.5 py-1.5 text-xs whitespace-nowrap text-white shadow-lg"
      }
    >
      {children}
    </div>
  );
}

/**
 * Infobulle qui parait au curseur.
 *
 * Elle parait des le survol, la ou l'infobulle native du navigateur se fait
 * attendre une seconde, et elle est montee dans un portail sur `body` : rendue
 * a l'interieur d'une cellule `sticky`, qui porte son propre contexte
 * d'empilement, elle passait sous la cellule de la ligne suivante et se
 * trouvait rognee.
 *
 * Le contenu est donne au survol et non a l'appel : une meme infobulle sert
 * ainsi plusieurs elements voisins, comme les pastilles d'intervenants.
 *
 * `riche` la fait passer du bandeau sombre d'un nom a une carte claire, ou du
 * contenu mis en forme se rend tel qu'il s'ecrit. Elle s'y fige a la premiere
 * apparition plutot que de suivre le curseur : un paragraphe qu'on lit ne doit
 * pas bouger sous les yeux.
 */
export function useTooltipCurseur({ riche = false }: { riche?: boolean } = {}) {
  const [etat, setEtat] = useState<Etat | null>(null);

  const tooltip = etat
    ? createPortal(
        <Bulle key={`${etat.x},${etat.y}`} {...etat} riche={riche}>
          {etat.contenu}
        </Bulle>,
        document.body,
      )
    : null;

  return {
    tooltip,
    suivre: (event: MouseEvent, contenu: ReactNode) => {
      const position = { x: event.clientX, y: event.clientY, contenu };
      setEtat((precedent) => (riche && precedent ? precedent : position));
    },
    quitter: () => setEtat(null),
  };
}
