"use client";

import type { ProjectLinkResponse } from "@/lib/api/generated/model";
import { iconGlyph, iconLabel } from "@/lib/link-icons";

/** Past this many, the cell says how many are left rather than overflowing. */
const VISIBLE = 3;

interface ProjectLinksProps {
  links: ProjectLinkResponse[];
}

/**
 * The addresses attached to a mission, as icons.
 *
 * In a row there is no room for their labels: the icon says the family — a
 * repository, a mockup, a ticket — and the label comes back on hover. A
 * mission without any leaves the cell empty rather than drawing a placeholder:
 * only what can be read belongs in a table.
 *
 * The click opens the address and nothing else: without stopping it, the row
 * would open the mission panel underneath at the same time.
 */
export function ProjectLinks({ links }: ProjectLinksProps) {
  if (links.length === 0) return null;

  const shown = links.slice(0, VISIBLE);
  const rest = links.length - shown.length;

  return (
    <span className="flex items-center gap-1.5">
      {shown.map((link) => {
        const Glyph = iconGlyph(link.icon);
        return (
          <a
            key={link.id}
            href={link.url}
            target="_blank"
            rel="noreferrer noopener"
            title={link.label}
            aria-label={`${link.label} (${iconLabel(link.icon)})`}
            onClick={(event) => event.stopPropagation()}
            className="cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
          >
            <Glyph className="size-4 shrink-0" aria-hidden />
          </a>
        );
      })}

      {rest > 0 && (
        <span
          title={links
            .slice(VISIBLE)
            .map((link) => link.label)
            .join("\n")}
          className="text-xs text-slate-400"
        >
          +{rest}
        </span>
      )}
    </span>
  );
}
