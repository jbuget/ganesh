"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { MarkdownView } from "@/components/atoms/MarkdownView";
import { DescriptionComposer } from "@/components/molecules/DescriptionComposer";

interface ProjectDescriptionTabProps {
  description: string | null;
  saveDescription: (body: string) => Promise<void>;
}

/**
 * What the mission is, in the team's own words.
 *
 * It sits before everything else: one reads what a project is before reading
 * where it stands, and the catalogue publishes the same text without owning it.
 * Read rendered, written on demand.
 */
export function ProjectDescriptionTab({
  description,
  saveDescription,
}: ProjectDescriptionTabProps) {
  const [editing, setEditing] = useState(false);

  if (editing) {
    return (
      <DescriptionComposer
        value={description ?? ""}
        onCancel={() => setEditing(false)}
        onSave={async (body) => {
          await saveDescription(body);
          setEditing(false);
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="flex cursor-pointer items-center gap-1.5 text-sm text-slate-400 transition-colors hover:text-slate-700"
      >
        <Pencil className="size-3.5" aria-hidden />
        {description ? "Modifier" : "Rédiger la fiche"}
      </button>

      {description ? (
        <MarkdownView body={description} />
      ) : (
        <p className="text-sm text-slate-400">
          Aucune fiche. Décrivez le problème, la solution et ce que le service couvre.
        </p>
      )}
    </div>
  );
}
