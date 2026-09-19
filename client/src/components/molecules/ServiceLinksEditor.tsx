"use client";

import { InlineTextField } from "@/components/atoms/InlineTextField";
import { SheetRow } from "@/components/atoms/SheetRow";
import type { ProjectResponse } from "@/lib/api/generated/model";
import { SERVICE_LINKS, type ServiceLinkField } from "@/lib/service-sheet";

interface ServiceLinksEditorProps {
  project: ProjectResponse;
  onChange: (fields: Partial<Record<ServiceLinkField, string | null>>) => Promise<void>;
}

/**
 * The named addresses of a service, each on its own row.
 *
 * They are not a free list: the catalogue shows them in fixed places, so the
 * sheet asks for them one by one under the name the catalogue will use. What
 * does not fit here goes to the secondary links underneath.
 */
export function ServiceLinksEditor({ project, onChange }: ServiceLinksEditorProps) {
  return (
    <div className="divide-y divide-slate-100">
      {SERVICE_LINKS.map(({ field, label }) => (
        <SheetRow key={field} title={label}>
          <InlineTextField
            value={project[field]}
            label={label}
            placeholder="https://…"
            onChange={(url) => onChange({ [field]: url })}
          />
        </SheetRow>
      ))}
    </div>
  );
}
