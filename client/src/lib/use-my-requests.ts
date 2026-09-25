"use client";

import { useQueryClient } from "@tanstack/react-query";

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

  return {
    requests,
    isLoading,

    find: (requestId: number) =>
      requests.find((request) => request.id === requestId) ?? null,

    async file(draft: {
      title: string;
      departments: Department[];
      sponsor_ids: number[];
    }) {
      const filed = mutationResult<RequestResponse>(await fileRequest(draft));
      await queryClient.invalidateQueries();
      // Handed back so the screen can open it: the dialog asked for three
      // things, and the rest of the sheet is what one came to write.
      return filed;
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
        desired_timing: request.desired_timing ?? null,
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
    },
  };
}
