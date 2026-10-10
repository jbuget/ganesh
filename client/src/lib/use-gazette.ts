"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { useGenerateDigest } from "@/lib/api/generated/gazette/gazette";
import type { DigestResponse } from "@/lib/api/generated/model";
import { mutationResult, useDigest, useProjects } from "@/lib/api/queries";
import {
  currentMonth,
  firstDayOfMonth,
  monthParam,
  nextMonth,
  parseMonthParam,
  previousMonth,
} from "@/lib/dates";
import { generationRefusal } from "@/lib/gazette";
import { useQueryString, writeUrl } from "@/lib/url-state";

/**
 * State and actions of La Gazette.
 *
 * All the coordination lives here — which month, which generation, asking for
 * a fresh one — so the component carries nothing but the rendering.
 */
export function useGazette() {
  // The month and the version live in the address: a digest is something one
  // sends a link to, and the link has to open on what its sender was reading.
  // Absent, the month is the one running.
  const query = useQueryString();
  const params = new URLSearchParams(query);
  const cursor = parseMonthParam(params.get("month")) ?? currentMonth();
  const asked = Number(params.get("version")) || null;

  const month = firstDayOfMonth(cursor.year, cursor.month);
  const queryClient = useQueryClient();

  const { digest, isLoading } = useDigest(month, asked);
  const generate = useGenerateDigest();
  const [refusal, setRefusal] = useState<string | null>(null);

  // Every project the register knows, archived ones included: the model read
  // some that have no chapter of their own, and a name is set in bold wherever
  // the text carries it.
  const { projects } = useProjects(true);

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
    referenceLabels: projects.map((project) => project.label),
    /** Why the last request for a digest came to nothing, until the next one. */
    refusal,

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
      setRefusal(null);
      try {
        const response = await generate.mutateAsync({ data: { month } });
        const fresh = mutationResult<DigestResponse>(response);
        await queryClient.invalidateQueries();
        show(fresh.version ?? 1);
      } catch (error) {
        // Somebody else generated the month first: what was asked for is
        // already there, so the screen goes to the latest version rather than
        // leaving the reader on one that is no longer the newest.
        setRefusal(generationRefusal(error));
        await queryClient.invalidateQueries();
        writeUrl((params) => params.delete("version"));
      }
    },
  };
}
