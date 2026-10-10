"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getDigest, useGenerateDigest } from "@/lib/api/generated/gazette/gazette";
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
import { awaitNewVersion } from "@/lib/await-new-version";
import { generationRefusal, lateVersion, mayHaveFinishedAnyway } from "@/lib/gazette";
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
  // Looking for a version the request gave up on: the generation is still, as
  // far as the reader is concerned, under way.
  const [isWaiting, setWaiting] = useState(false);

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

  /**
   * What the screen does when asking for a digest came to an error.
   *
   * A refusal — somebody else generated the month first, say — means nothing
   * was written, and the screen goes to the latest version rather than leaving
   * the reader on one that is no longer the newest. Anything else may be an
   * answer that never got back: the host in front of the API cuts a request
   * off at thirty seconds and the API goes on and writes the version
   * regardless. Ask the server before saying it failed.
   */
  async function recoverFrom(error: unknown) {
    if (!mayHaveFinishedAnyway(error)) {
      setRefusal(generationRefusal(error));
      await queryClient.invalidateQueries();
      writeUrl((params) => params.delete("version"));
      return;
    }

    setWaiting(true);
    const appeared = await awaitNewVersion({
      before: digest?.versions[0]?.version ?? 0,
      readLatest: async () =>
        mutationResult<DigestResponse>(await getDigest({ month })).version ?? 0,
    }).finally(() => setWaiting(false));
    await queryClient.invalidateQueries();

    if (appeared === null) {
      setRefusal(generationRefusal(error));
      return;
    }
    setRefusal(lateVersion(appeared));
    show(appeared);
  }

  return {
    cursor,
    digest,
    isLoading,
    isGenerating: generate.isPending || isWaiting,
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
        await recoverFrom(error);
      }
    },
  };
}
