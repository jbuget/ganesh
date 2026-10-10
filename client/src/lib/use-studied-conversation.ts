"use client";

import { useQueryClient } from "@tanstack/react-query";

import {
  annotateAssistantExchange,
  getListAssistantConversationsQueryKey,
  getReadAssistantConversationQueryKey,
  getReadAssistantIndicatorsQueryKey,
} from "@/lib/api/generated/admin/admin";
import type { Cause } from "@/lib/api/generated/model";
import { useAssistantConversation } from "@/lib/api/queries";

/**
 * A conversation opened for study, and the annotation left under its answers.
 *
 * Annotating moves three readings at once — the conversation, the count of
 * annotated answers in the table, the causes in the indicators — so all
 * three are read again, and nothing else of the application is.
 */
export function useStudiedConversation(conversationId: string | null) {
  const queryClient = useQueryClient();
  const { conversation, isLoading } = useAssistantConversation(conversationId);

  return {
    conversation,
    isLoading,

    async annotate(exchangeId: number, cause: Cause, note: string) {
      await annotateAssistantExchange(exchangeId, { cause, note });
      await Promise.all(
        [
          getReadAssistantConversationQueryKey(conversationId ?? ""),
          getListAssistantConversationsQueryKey(),
          getReadAssistantIndicatorsQueryKey(),
        ].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
      );
    },
  };
}
