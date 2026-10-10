"use client";

import { useQueryString, writeUrl } from "@/lib/url-state";

const PARAM = "conversation";

/**
 * The conversation open in the side panel, held by the URL.
 *
 * As the teammate's panel is: a conversation worth discussing is sent by a
 * link, survives a reload, and going back closes it.
 */
export function useOpenedConversation() {
  const params = new URLSearchParams(useQueryString());

  return {
    openedConversation: params.get(PARAM),

    open(conversationId: string) {
      writeUrl((params) => params.set(PARAM, conversationId));
    },

    close() {
      writeUrl((params) => params.delete(PARAM));
    },
  };
}
