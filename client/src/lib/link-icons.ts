import {
  FileText,
  Folder,
  Frame,
  GitBranch,
  Link as PlainLink,
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
export const LINK_ICONS: {
  value: LinkIcon;
  label: string;
  glyph: LucideIcon;
}[] = [
  { value: "link", label: "Lien", glyph: PlainLink },
  { value: "document", label: "Document", glyph: FileText },
  { value: "spreadsheet", label: "Tableur", glyph: Table2 },
  { value: "presentation", label: "Présentation", glyph: Presentation },
  { value: "folder", label: "Dossier", glyph: Folder },
  { value: "design", label: "Maquette", glyph: Frame },
  { value: "repository", label: "Dépôt de code", glyph: GitBranch },
  { value: "ticket", label: "Ticket", glyph: Ticket },
  { value: "discussion", label: "Discussion", glyph: MessagesSquare },
  { value: "video", label: "Vidéo", glyph: Video },
];

const PAR_VALEUR = new Map(LINK_ICONS.map((icon) => [icon.value, icon]));

/** Le dessin d'une icone. Une valeur inconnue retombe sur le lien generique. */
export function iconGlyph(value: LinkIcon): LucideIcon {
  return PAR_VALEUR.get(value)?.glyph ?? PlainLink;
}

/** Le nom lisible d'une icone, pour les lecteurs d'ecran et le selecteur. */
export function libelleIcone(value: LinkIcon): string {
  return PAR_VALEUR.get(value)?.label ?? "Lien";
}
