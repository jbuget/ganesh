"use client";

import { Check, Plus, Search } from "lucide-react";
import { useState } from "react";

import { TagMark } from "@/components/atoms/TagMark";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { TagResponse } from "@/lib/api/generated/model";
import { useTags } from "@/lib/api/queries";
import { proposesCreating, tagFailureSaid } from "@/lib/tags";

interface TagPickerProps {
  /** The tags the project carries. */
  tags: TagResponse[];
  /** Puts a tag on by the name typed: the server opens it if nobody had. */
  onAdd: (name: string) => Promise<void>;
  onRemove: (tagId: number) => Promise<void>;
}

/**
 * The tags of a project, to read and to change.
 *
 * Each tag carries its own cross, so taking one off is a click and nothing
 * more. Putting one on opens a list of the tags in use, the closest to what is
 * typed first: picking one that exists is the way in, and opening a new one is
 * a gesture of its own at the foot of the list — never a side effect of
 * typing, which is how « IA », « ia » and « intelligence artificielle » end up
 * three tags.
 */
export function TagPicker({ tags, onAdd, onRemove }: TagPickerProps) {
  const [isOpen, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [failure, setFailure] = useState<string | null>(null);
  const { tags: found } = useTags(search, isOpen);
  const carried = new Set(tags.map((tag) => tag.id));
  const typed = search.trim();

  async function attempt(action: () => Promise<void>) {
    try {
      await action();
      setFailure(null);
    } catch (error) {
      setFailure(tagFailureSaid(error));
    }
  }

  async function add(name: string) {
    await attempt(() => onAdd(name));
    setSearch("");
  }

  function toggle(tag: { id: number; name: string }) {
    return carried.has(tag.id) ? attempt(() => onRemove(tag.id)) : add(tag.name);
  }

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      {tags.map((tag) => (
        <TagMark
          key={tag.id}
          tag={tag}
          onRemove={() => void attempt(() => onRemove(tag.id))}
        />
      ))}

      <Popover
        open={isOpen}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) {
            setSearch("");
            setFailure(null);
          }
        }}
      >
        <PopoverTrigger
          aria-label="Ajouter un tag"
          className={`flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-100 ${
            tags.length === 0 ? "-mx-1 text-slate-400" : "text-slate-400"
          }`}
        >
          <Plus className="size-3.5" aria-hidden />
          {tags.length === 0 && "Ajouter un tag"}
        </PopoverTrigger>

        <PopoverContent align="start" className="w-64 gap-0 p-1">
          <div className="-mx-1 flex items-center gap-2 border-b border-border px-2.5">
            <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            <input
              type="text"
              autoFocus
              value={search}
              aria-label="Rechercher un tag"
              placeholder="Rechercher ou créer…"
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && typed) {
                  event.preventDefault();
                  void add(typed);
                }
              }}
              className="h-8 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>

          <ul className="max-h-64 overflow-y-auto overscroll-contain pt-1">
            {found.map((tag) => {
              const present = carried.has(tag.id);
              return (
                <li key={tag.id}>
                  <button
                    type="button"
                    aria-pressed={present}
                    onClick={() => void toggle(tag)}
                    className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100"
                  >
                    <span className="min-w-0 flex-1">
                      <TagMark tag={tag} />
                    </span>
                    <span className="shrink-0 text-xs text-slate-400">
                      {tag.project_count} projet{tag.project_count > 1 ? "s" : ""}
                    </span>
                    {present && (
                      <Check className="size-4 shrink-0 text-sky-600" aria-hidden />
                    )}
                  </button>
                </li>
              );
            })}

            {proposesCreating(search, found) && (
              <li>
                <button
                  type="button"
                  onClick={() => void add(typed)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-slate-700 transition-colors hover:bg-slate-100"
                >
                  <Plus className="size-3.5 shrink-0" aria-hidden />
                  Créer le tag « {typed} »
                </button>
              </li>
            )}
          </ul>

          {found.length === 0 && !typed && (
            <p className="px-2 py-6 text-center text-sm text-muted-foreground">
              Aucun tag pour l&apos;instant. Tapez-en un pour le créer.
            </p>
          )}

          {failure && (
            <p role="alert" className="px-2 py-1.5 text-xs text-red-600">
              {failure}
            </p>
          )}
        </PopoverContent>
      </Popover>
    </div>
  );
}
