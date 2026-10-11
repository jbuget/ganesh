"use client";

import { TagManagerRow } from "@/components/molecules/TagManagerRow";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useTags } from "@/lib/api/queries";
import { useTagManagement } from "@/lib/use-tag-management";

interface TagManagerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * The vocabulary of tags, for a manager to look after.
 *
 * Anybody opens a tag by typing it on a project; what keeps the vocabulary
 * from drifting is that a manager can rename it, recolour it, and fold a
 * duplicate into the tag it should have been. The list is read from the tags
 * in use, the most carried first: a tag nobody carries any more is nothing to
 * look after.
 */
export function TagManagerDialog({ open, onOpenChange }: TagManagerDialogProps) {
  const { tags } = useTags("", open);
  const management = useTagManagement();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Gérer les tags</DialogTitle>
          <DialogDescription>
            Renommer, recolorer ou fusionner un tag change tous les projets qui le
            portent. Fusionner ne se défait pas.
          </DialogDescription>
        </DialogHeader>

        {tags.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Aucun tag n&apos;est posé pour l&apos;instant.
          </p>
        ) : (
          <ul className="max-h-[60vh] divide-y divide-slate-100 overflow-y-auto overscroll-contain">
            {tags.map((tag) => (
              <TagManagerRow
                key={tag.id}
                tag={tag}
                others={tags.filter((other) => other.id !== tag.id)}
                onRename={(name) => management.rename(tag.id, name)}
                onRecolor={(color) => management.recolor(tag.id, color)}
                onMerge={(targetId) => management.merge(tag.id, targetId)}
              />
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}
