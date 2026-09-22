"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type {
  Department,
  FillInRequestRequest,
  RequestResponse,
} from "@/lib/api/generated/model";
import {
  deleteRequest,
  fileRequest,
  fillInRequest,
  submitRequest,
  withdrawRequest,
} from "@/lib/api/generated/requests/requests";
import { mutationResult, useMyRequests } from "@/lib/api/queries";

/**
 * State and actions of the screen one files a need on.
 *
 * The sheet goes to the API whole — what is left out is emptied — so a change
 * to one field carries the others as they stand, exactly as a teammate's
 * identity sheet does.
 */
export function useMyRequestsScreen() {
  const queryClient = useQueryClient();
  const { requests, isLoading } = useMyRequests();
  const [openedId, setOpened] = useState<number | null>(null);

  const opened = requests.find((request) => request.id === openedId) ?? null;

  return {
    requests,
    isLoading,
    opened,
    open: (requestId: number) => setOpened(requestId),
    close: () => setOpened(null),

    async file(draft: {
      title: string;
      departments: Department[];
      sponsor_ids: number[];
    }) {
      const filed = mutationResult<RequestResponse>(await fileRequest(draft));
      await queryClient.invalidateQueries();
      // Opened straight away: the dialog asked for three things, and the rest
      // of the sheet is what one came to write.
      setOpened(filed.id);
    },

    async fillIn(request: RequestResponse, change: Partial<FillInRequestRequest>) {
      await fillInRequest(request.id, {
        title: request.title,
        departments: request.departments,
        sponsor_ids: request.sponsors.map((sponsor) => sponsor.id),
        problem: request.problem ?? null,
        impact: request.impact ?? null,
        expected_outcome: request.expected_outcome ?? null,
        cost_of_inaction: request.cost_of_inaction ?? null,
        desired_by: request.desired_by ?? null,
        envisaged_solution: request.envisaged_solution ?? null,
        ...change,
      });
      await queryClient.invalidateQueries();
    },

    async submit(requestId: number) {
      await submitRequest(requestId);
      await queryClient.invalidateQueries();
    },

    async withdraw(requestId: number) {
      await withdrawRequest(requestId);
      await queryClient.invalidateQueries();
    },

    async remove(requestId: number) {
      await deleteRequest(requestId);
      await queryClient.invalidateQueries();
      setOpened(null);
    },
  };
}
