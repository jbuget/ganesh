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
 * The families of links in the reference list, and the shape they take on screen.
 *
 * The catalogue comes from the server: this file only gives it a drawing and a
 * readable name. The order is that of the picker — the plain link first, then
 * the families from the most common to the rarest.
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

/** The drawing of an icon. An unknown value falls back to the plain link. */
export function iconGlyph(value: LinkIcon): LucideIcon {
  return PAR_VALEUR.get(value)?.glyph ?? PlainLink;
}

/** The readable name of an icon, for screen readers and the picker. */
export function iconLabel(value: LinkIcon): string {
  return PAR_VALEUR.get(value)?.label ?? "Lien";
}
