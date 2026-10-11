"use client";

import { useQueryClient } from "@tanstack/react-query";

import type { TagColor } from "@/lib/api/generated/model";
import { mergeTags, recolorTag, renameTag } from "@/lib/api/generated/tags/tags";

/**
 * What a manager does to the vocabulary of tags.
 *
 * Each gesture moves every project carrying the tag, so every screen reading
 * them is told to read again: the reference list and the board sit behind the
 * dialog, and would go on showing the old name. A refusal goes through — the
 * row that asked says why.
 */
export function useTagManagement() {
  const queryClient = useQueryClient();

  async function changed() {
    await queryClient.invalidateQueries();
  }

  return {
    async rename(tagId: number, name: string) {
      await renameTag(tagId, { name });
      await changed();
    },

    async recolor(tagId: number, color: TagColor) {
      await recolorTag(tagId, { color });
      await changed();
    },

    /** Folds `tagId` into `targetId`: the first is gone afterwards. */
    async merge(tagId: number, targetId: number) {
      await mergeTags(tagId, { target_id: targetId });
      await changed();
    },
  };
}
