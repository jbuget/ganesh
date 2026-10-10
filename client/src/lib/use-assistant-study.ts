"use client";

import { useCallback, useState } from "react";

import { getExportAssistantExchangesUrl } from "@/lib/api/generated/admin/admin";
import type {
  ExportFormat,
  UnansweredQuestionResponse,
} from "@/lib/api/generated/model";
import {
  useAssistantConversations,
  useAssistantIndicators,
  useAssistantUnanswered,
  useProjects,
  useTeammates,
} from "@/lib/api/queries";
import {
  NO_STUDY_FILTER,
  type StudyFilters,
  asStudyQuery,
} from "@/lib/assistant-study";

/** How many conversations a page of the table holds. */
export const STUDY_PAGE = 50;

/**
 * The state of the assistant's tab in the administration.
 *
 * One set of criteria reads the table, the indicators and the export: the
 * figure above the table and the file saved beside it must count the same
 * exchanges. Changing a criterion goes back to the first page — the second
 * page of another question is not where anybody meant to land.
 *
 * People and projects come over as identifiers and are named here, from the
 * lists the screen already holds.
 */
export function useAssistantStudy() {
  const [filters, setFilters] = useState<StudyFilters>(NO_STUDY_FILTER);
  const [pageIndex, setPageIndex] = useState(0);
  const criteria = asStudyQuery(filters);

  const { page, isLoading } = useAssistantConversations({
    ...criteria,
    limit: STUDY_PAGE,
    offset: pageIndex * STUDY_PAGE,
  });
  const { indicators } = useAssistantIndicators(criteria);
  // The latest page alone: they are read to see what fails, not counted
  // through — the count is in the indicators.
  const { page: unansweredPage } = useAssistantUnanswered({
    ...criteria,
    limit: STUDY_PAGE,
    offset: 0,
  });
  const [openedUnanswered, setOpenedUnanswered] = useState<number | null>(null);
  const unanswered = unansweredPage?.questions ?? [];
  // Deactivated accounts and archived projects included: they asked, and were
  // asked about, while they were here.
  const { teammates } = useTeammates(true);
  const { projects } = useProjects(true);

  const change = useCallback((over: Partial<StudyFilters>) => {
    setFilters((current) => ({ ...current, ...over }));
    setPageIndex(0);
  }, []);

  const clear = useCallback(() => {
    setFilters(NO_STUDY_FILTER);
    setPageIndex(0);
  }, []);

  const total = page?.total ?? 0;

  return {
    filters,
    change,
    clear,
    isLoading,
    conversations: page?.conversations ?? [],
    unanswered,
    unansweredTotal: unansweredPage?.total ?? 0,
    openedUnanswered:
      unanswered.find(
        (held): held is UnansweredQuestionResponse => held.id === openedUnanswered,
      ) ?? null,
    openUnanswered: setOpenedUnanswered,
    closeUnanswered: () => setOpenedUnanswered(null),
    indicators,
    total,
    firstShown: total === 0 ? 0 : pageIndex * STUDY_PAGE + 1,
    lastShown: Math.min((pageIndex + 1) * STUDY_PAGE, total),
    hasPrevious: pageIndex > 0,
    hasNext: (pageIndex + 1) * STUDY_PAGE < total,
    previous: () => setPageIndex((index) => Math.max(0, index - 1)),
    next: () => setPageIndex((index) => index + 1),

    askerName: (askerId: number) =>
      teammates.find((person) => person.id === askerId)?.display_name ??
      `Compte n° ${askerId}`,
    projectLabel: (projectId: number) =>
      projects.find((project) => project.id === projectId)?.label ??
      `Projet n° ${projectId}`,
    teammates,

    /** An address the browser saves, through the BFF like every other call. */
    exportUrl: (format: ExportFormat) =>
      getExportAssistantExchangesUrl({ ...criteria, format }),
  };
}
