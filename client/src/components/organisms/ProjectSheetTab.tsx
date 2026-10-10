"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { InlineTextField } from "@/components/atoms/InlineTextField";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { OptionPicker } from "@/components/atoms/OptionPicker";
import { RichTextEditor } from "@/components/atoms/RichTextEditor";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { TagListField } from "@/components/atoms/TagListField";
import { ToggleField } from "@/components/atoms/ToggleField";
import { ProjectDependencies } from "@/components/molecules/ProjectDependencies";
import { ProjectLinksEditor } from "@/components/molecules/ProjectLinksEditor";
import { ServiceLinksEditor } from "@/components/molecules/ServiceLinksEditor";
import { Button } from "@/components/ui/button";
import type { LinkIcon, ProjectDetailResponse } from "@/lib/api/generated/model";
import {
  CRITICALITIES,
  SERVICE_TYPES,
  frenchList,
  CATALOG_ADDRESS,
  publicationBlockers,
  slugError,
  suggestSlug,
  type SheetFields,
} from "@/lib/service-sheet";

interface ProjectSheetTabProps {
  detail: ProjectDetailResponse;
  updateFields: (fields: SheetFields) => Promise<void>;
  saveDescription: (body: string) => Promise<void>;
  saveRegistry: (registry: {
    stack: string[];
    tags: string[];
    depends_on: number[];
  }) => Promise<void>;
  addLink: (label: string, url: string, icon: LinkIcon | null) => Promise<void>;
  removeLink: (linkId: number) => Promise<void>;
}

/** Writing the body of the sheet, with the headings that structure it. */
function Composer({
  value,
  onSave,
  onCancel,
}: {
  value: string;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}) {
  const [body, setBody] = useState(value);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await onSave(body);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <RichTextEditor
        value={value}
        withHeadings
        fullHeight
        placeholder="Le problème, la solution, ce que le service couvre…"
        onChange={setBody}
        onSubmit={() => void save()}
      />
      <div className="flex shrink-0 items-center gap-2">
        <Button size="sm" disabled={busy} onClick={() => void save()}>
          Enregistrer
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
        <span className="text-xs text-slate-400">⌘↵ pour enregistrer</span>
      </div>
    </div>
  );
}

/** The full text of the sheet: read rendered, written on demand. */
function Body({
  description,
  onSave,
}: {
  description: string | null;
  onSave: (body: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);

  if (editing) {
    return (
      <Composer
        value={description ?? ""}
        onCancel={() => setEditing(false)}
        onSave={async (body) => {
          await onSave(body);
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

/**
 * The mission as the service catalogue will publish it.
 *
 * Everything waat.tools reads lives here and nowhere else: the pilotage tab
 * steers the mission, this one describes the service it produces. Each field
 * saves as it is left — there is no « Enregistrer » for the sheet, only for
 * the long text, which one writes in one go.
 */
export function ProjectSheetTab({
  detail,
  updateFields,
  saveDescription,
  saveRegistry,
  addLink,
  removeLink,
}: ProjectSheetTabProps) {
  const { project } = detail;
  const blockers = publicationBlockers(project);
  const suggested = suggestSlug(project.label);

  /** The three lists travel together: one of them changes, all three are sent. */
  function registry(changed: {
    stack?: string[];
    tags?: string[];
    depends_on?: number[];
  }) {
    return saveRegistry({
      stack: changed.stack ?? detail.stack,
      tags: changed.tags ?? detail.tags,
      depends_on:
        changed.depends_on ?? detail.dependencies.map((mission) => mission.id),
    });
  }

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <SheetSectionTitle>Publication</SheetSectionTitle>

        <div className="divide-y divide-slate-100">
          <SheetRow title="Au catalogue">
            <ToggleField
              value={project.is_published}
              label="Publier au catalogue"
              onText="Publiée sur waat.tools"
              offText="Non publiée"
              blockedBy={
                blockers.length > 0 ? `Il manque ${frenchList(blockers)}.` : null
              }
              onChange={(is_published) => updateFields({ is_published })}
            />
          </SheetRow>

          <SheetRow title="Slug">
            <InlineTextField
              value={project.slug}
              label="Slug"
              prefix={CATALOG_ADDRESS}
              placeholder="portail-bailleurs"
              suggestion={suggested || null}
              validate={slugError}
              onChange={(slug) => updateFields({ slug })}
            />
          </SheetRow>

          <SheetRow title="Résumé">
            <InlineTextField
              value={project.summary}
              label="Résumé"
              placeholder="Ce que le service fait, en une phrase."
              onChange={(summary) => updateFields({ summary })}
            />
          </SheetRow>
        </div>
      </section>

      <section className="space-y-2">
        <SheetSectionTitle>Fiche</SheetSectionTitle>
        <Body description={project.description} onSave={saveDescription} />
      </section>

      <section className="space-y-2">
        <SheetSectionTitle>Liens</SheetSectionTitle>
        <ServiceLinksEditor project={project} onChange={updateFields} />
        <div className="pt-1">
          <p className="pb-1.5 text-sm text-slate-500">Autres liens</p>
          <ProjectLinksEditor
            links={detail.links}
            onAdd={addLink}
            onRemove={removeLink}
          />
        </div>
      </section>

      <section className="space-y-2">
        <SheetSectionTitle>Technique</SheetSectionTitle>

        <div className="divide-y divide-slate-100">
          <SheetRow title="Type">
            <OptionPicker
              value={project.service_type}
              options={SERVICE_TYPES}
              label="Type"
              onChange={(service_type) => updateFields({ service_type })}
            />
          </SheetRow>

          <SheetRow title="Criticité">
            <OptionPicker
              value={project.criticality}
              options={CRITICALITIES}
              label="Criticité"
              onChange={(criticality) => updateFields({ criticality })}
            />
          </SheetRow>

          <SheetRow title="Stack">
            <TagListField
              values={detail.stack}
              label="Stack"
              placeholder="Next.js"
              onChange={(stack) => registry({ stack })}
            />
          </SheetRow>

          <SheetRow title="Hébergement">
            <InlineTextField
              value={project.hosting}
              label="Hébergement"
              placeholder="AWS"
              onChange={(hosting) => updateFields({ hosting })}
            />
          </SheetRow>

          <SheetRow title="Entra ID">
            <ToggleField
              value={project.has_microsoft_entra}
              label="Authentification Entra ID"
              onText="Authentification Entra ID"
              offText="Sans Entra ID"
              onChange={(has_microsoft_entra) => updateFields({ has_microsoft_entra })}
            />
          </SheetRow>

          <SheetRow title="Dépend de">
            <ProjectDependencies
              projectId={project.id}
              dependencies={detail.dependencies}
              onChange={(depends_on) => registry({ depends_on })}
            />
          </SheetRow>
        </div>
      </section>

      <section className="space-y-2">
        <SheetSectionTitle>Rattachement</SheetSectionTitle>

        <div className="divide-y divide-slate-100">
          <SheetRow title="Équipe">
            <InlineTextField
              value={project.team}
              label="Équipe"
              placeholder="Infra & Ops"
              onChange={(team) => updateFields({ team })}
            />
          </SheetRow>

          <SheetRow title="Canal Slack">
            <InlineTextField
              value={project.slack_channel}
              label="Canal Slack"
              placeholder="#team-infra"
              onChange={(slack_channel) => updateFields({ slack_channel })}
            />
          </SheetRow>

          <SheetRow title="Tags">
            <TagListField
              values={detail.tags}
              label="Tags"
              placeholder="monitoring"
              onChange={(tags) => registry({ tags })}
            />
          </SheetRow>
        </div>
      </section>
    </div>
  );
}
