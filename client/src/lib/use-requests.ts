"use client";

import { useQueryClient } from "@tanstack/react-query";

import type {
  FillInRequestRequest,
  ProjectKind,
  RequestResponse,
  RequestState,
} from "@/lib/api/generated/model";
import {
  convertRequest,
  decideRequest,
  deleteRequest,
  fileRequest,
  fillInRequest,
  submitRequest,
  withdrawRequest,
} from "@/lib/api/generated/requests/requests";
import { mutationResult, useCurrentUser, useRequests } from "@/lib/api/queries";
import { filterRequests, type RequestFilters } from "@/lib/request-filters";

/**
 * State and actions of the screen the team weighs needs on.
 *
 * The whole list is read and narrowed here: forty needs are nothing to filter
 * in the browser, and every criterion then answers as one types rather than
 * after a round trip.
 */
export function useRequestsScreen(filters: RequestFilters) {
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const { requests, isLoading } = useRequests();

  const visible = filterRequests(requests, filters);

  return {
    requests: visible,
    isLoading,
    user,
    visible: visible.length,
    total: requests.length,

    find: (requestId: number) =>
      requests.find((request) => request.id === requestId) ?? null,

    async file(draft: Parameters<typeof fileRequest>[0]) {
      const filed = mutationResult<RequestResponse>(await fileRequest(draft));
      await queryClient.invalidateQueries();
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
    },

    async convert(requestId: number, kind: ProjectKind, parentId: number | null) {
      await convertRequest(requestId, { kind, parent_id: parentId });
      await queryClient.invalidateQueries();
    },

    async decide(requestId: number, decision: RequestState, note: string | null) {
      await decideRequest(requestId, { decision, note });
      await queryClient.invalidateQueries();
    },
  };
}
