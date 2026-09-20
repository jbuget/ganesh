"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useGenerateDigest } from "@/lib/api/generated/gazette/gazette";
import type { DigestResponse } from "@/lib/api/generated/model";
import { mutationResult, useDigest } from "@/lib/api/queries";
import {
  firstDayOfMonth,
  monthParam,
  nextMonth,
  parseMonthParam,
  previousMonth,
  todayIso,
} from "@/lib/dates";
import { useQueryString, writeUrl } from "@/lib/url-state";

/**
 * State and actions of La Gazette.
 *
 * All the coordination lives here — which month, which generation, asking for
 * a fresh one — so the component carries nothing but the rendering.
 */
export function useGazette() {
  const today = todayIso();
  // The month and the version live in the address: a digest is something one
  // sends a link to, and the link has to open on what its sender was reading.
  // Absent, the month is the one running.
  const query = useQueryString();
  const params = new URLSearchParams(query);
  const cursor = parseMonthParam(params.get("month")) ?? {
    year: Number(today.slice(0, 4)),
    month: Number(today.slice(5, 7)),
  };
  const asked = Number(params.get("version")) || null;

  const month = firstDayOfMonth(cursor.year, cursor.month);
  const queryClient = useQueryClient();

  const { digest, isLoading } = useDigest(month, asked);
  const generate = useGenerateDigest();

  function goTo(next: { year: number; month: number }) {
    // The version is dropped on the way: a version number belongs to one
    // month, and carrying « version 3 » into another would open a digest
    // nobody asked to see — or none at all.
    writeUrl((params) => {
      params.set("month", monthParam(next));
      params.delete("version");
    });
  }

  function show(version: number) {
    writeUrl((params) => params.set("version", String(version)));
  }

  return {
    cursor,
    digest,
    isLoading,
    isGenerating: generate.isPending,

    goToPreviousMonth: () => goTo(previousMonth(cursor.year, cursor.month)),
    goToNextMonth: () => goTo(nextMonth(cursor.year, cursor.month)),
    openVersion: show,

    /**
     * Asks for a digest of the month on screen.
     *
     * One lands on the version just written rather than on whatever was being
     * read: what was asked for is what should appear.
     */
    async generateDigest() {
      const response = await generate.mutateAsync({ data: { month } });
      const fresh = mutationResult<DigestResponse>(response);
      await queryClient.invalidateQueries();
      show(fresh.version ?? 1);
    },
  };
}
