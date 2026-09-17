import {
  FileText,
  Folder,
  Frame,
  GitBranch,
  Link as LinkGenerique,
  MessagesSquare,
  Presentation,
  Table2,
  Ticket,
  Video,
  type LucideIcon,
} from "lucide-react";

import type { LinkIcon } from "@/lib/api/generated/model";

/**
 * Les familles de liens du referentiel, et la forme qu'elles prennent a l'ecran.
 *
 * Le catalogue vient du serveur : ce fichier ne fait que lui donner un dessin
 * et un nom lisible. L'ordre est celui du selecteur — le lien generique en
 * tete, puis les familles de la plus courante a la plus rare.
 */
export const ICONES_DE_LIEN: {
  valeur: LinkIcon;
  libelle: string;
  Dessin: LucideIcon;
}[] = [
  { valeur: "lien", libelle: "Lien", Dessin: LinkGenerique },
  { valeur: "document", libelle: "Document", Dessin: FileText },
  { valeur: "tableur", libelle: "Tableur", Dessin: Table2 },
  { valeur: "presentation", libelle: "Présentation", Dessin: Presentation },
  { valeur: "dossier", libelle: "Dossier", Dessin: Folder },
  { valeur: "maquette", libelle: "Maquette", Dessin: Frame },
  { valeur: "depot", libelle: "Dépôt de code", Dessin: GitBranch },
  { valeur: "ticket", libelle: "Ticket", Dessin: Ticket },
  { valeur: "discussion", libelle: "Discussion", Dessin: MessagesSquare },
  { valeur: "video", libelle: "Vidéo", Dessin: Video },
];

const PAR_VALEUR = new Map(ICONES_DE_LIEN.map((icone) => [icone.valeur, icone]));

/** Le dessin d'une icone. Une valeur inconnue retombe sur le lien generique. */
export function dessinIcone(valeur: LinkIcon): LucideIcon {
  return PAR_VALEUR.get(valeur)?.Dessin ?? LinkGenerique;
}

/** Le nom lisible d'une icone, pour les lecteurs d'ecran et le selecteur. */
export function libelleIcone(valeur: LinkIcon): string {
  return PAR_VALEUR.get(valeur)?.libelle ?? "Lien";
}
