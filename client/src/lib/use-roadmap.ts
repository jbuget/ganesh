"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { readRoadmap } from "@/lib/api/generated/planning/planning";
import { updateProject } from "@/lib/api/generated/projects/projects";
import type { ReadRoadmapParams, RoadmapResponse } from "@/lib/api/generated/model";
import type { Criterion } from "@/lib/mission-filters";
import { readGrouping, readSpan, writeView, type Grouping } from "@/lib/roadmap";
import { useMissionFilters } from "@/lib/use-mission-filters";
import { writeUrl, useQueryString } from "@/lib/url-state";

/**
 * What the roadmap asks about, and what it deliberately does not.
 *
 * Publication is the catalogue's question, and the roadmap is shown to a
 * committee rather than used to tend waat.tools. « État » is left out for a
 * different reason: its empty value is not neutral on the board, which shows
 * active missions alone, whereas a roadmap reads the archived ones on
 * purpose — a service delivered in March belongs to the year whether or not
 * it is still on the reference list. And nobody asks a committee who is on
 * what, which is the plan's question.
 *
 * Declared here rather than at the call site: the filters are read against
 * this list, and one rebuilt on every render would hand back new filters
 * each time, which the reading would take for a change.
 */
const ROADMAP_CRITERIA: Criterion[] = [
  "name",
  "phases",
  "categories",
  "departments",
  "priorities",
  "types",
];

/**
 * How long a search waits before it is sent.
 *
 * The criteria are narrowed on the server, so a keystroke is a request. Long
 * enough that typing « bailleurs » asks once rather than nine times, short
 * enough that one does not wonder whether the screen heard.
 */
const SETTLING_DELAY = 300;

/**
 * State of the roadmap screen: a window, a grouping, criteria, and the
 * drawing.
 *
 * All four live in the address. A roadmap is prepared once — the phases that
 * matter, the right span — and shown from a link, to a committee or to a
 * department; a link restoring half of that would rebuild half a screen,
 * which is worse than rebuilding none of it.
 *
 * Unlike the grouping, which regroups what is already in hand, narrowing
 * costs a request: the tally above the bars is read off the lines the server
 * kept, and a figure counting forty missions above eight bars would be worse
 * than no figure at all.
 */
export function useRoadmapScreen() {
  const query = useQueryString();
  const params = useMemo(() => new URLSearchParams(query), [query]);
  const months = readSpan(params);
  const grouping = readGrouping(params);

  const { filters, hasFilter, set, clear } = useMissionFilters(ROADMAP_CRITERIA);

  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  //: The reading the drawing in hand answers, and the one that failed. Both
  //: hold a reading rather than a flag — see `reading` below.
  const [answered, setAnswered] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  //: Whether the last date posted was refused. Held apart from a read that
  //: failed: one leaves the screen empty, the other leaves it right and the
  //: write lost, and saying « erreur » for both would tell the reader nothing.
  const [saveFailed, setSaveFailed] = useState(false);

  //: The search as it stands once the typing has stopped. The address follows
  //: every keystroke, as it does on the board; only the request waits.
  const [settled, setSettled] = useState(filters.name);

  useEffect(() => {
    const timer = setTimeout(() => setSettled(filters.name), SETTLING_DELAY);
    return () => clearTimeout(timer);
  }, [filters.name]);

  /**
   * The reading being asked for, as one string.
   *
   * A reading is identified by its content, never by the object carrying it:
   * that object is rebuilt on every render — the address changes at every
   * keystroke, and with it every list of criteria — while what it asks stays
   * the same. Keying on the content is what keeps a re-render, or a letter
   * typed and wiped, from asking the server the same question twice.
   *
   * It is also what says whether the drawing in hand answers the question on
   * screen: `answered` and `failed` hold one, and comparing them to this needs
   * no flag kept in step with the request.
   */
  const reading = useMemo(() => {
    const asked: ReadRoadmapParams = {
      months,
      ...(settled.trim() ? { name: settled.trim() } : {}),
      ...(filters.phases.length ? { phase: filters.phases } : {}),
      ...(filters.categories.length ? { category: filters.categories } : {}),
      ...(filters.priorities.length ? { priority: filters.priorities } : {}),
      ...(filters.types.length ? { type: filters.types } : {}),
      ...(filters.departments.length ? { department: filters.departments } : {}),
    };
    return JSON.stringify(asked);
  }, [months, settled, filters]);

  const fetchReading = useCallback(
    (asked: string, isStillWanted: () => boolean = () => true) => {
      // The window itself is worked out by the server: where it opens and
      // how it lands on month boundaries is a rule, and a rule lives in one
      // place or it drifts.
      return readRoadmap(JSON.parse(asked) as ReadRoadmapParams)
        .then((response) => {
          if (!isStillWanted()) return;
          setRoadmap(response.data as RoadmapResponse);
          setAnswered(asked);
          setFailed(null);
        })
        .catch(() => {
          if (isStillWanted()) setFailed(asked);
        });
    },
    [],
  );

  useEffect(() => {
    let alive = true;
    void fetchReading(reading, () => alive);
    return () => {
      alive = false;
    };
  }, [reading, fetchReading]);

  function setView(change: { months?: number; grouping?: Grouping }) {
    writeUrl(
      (next) =>
        writeView(next, {
          months: change.months ?? months,
          grouping: change.grouping ?? grouping,
        }),
      "replace",
    );
  }

  return {
    roadmap,
    isLoading: answered !== reading && failed !== reading,
    hasError: failed === reading,
    months,
    setMonths: (span: number) => setView({ months: span }),
    grouping,
    setGrouping: (gathering: Grouping) => setView({ grouping: gathering }),
    filters,
    hasFilter,
    setFilters: set,
    clearFilters: clear,
    criteria: ROADMAP_CRITERIA,
    saveFailed,

    /** Reads the drawing again, after something changed it from elsewhere. */
    async refresh() {
      await fetchReading(reading);
    },

    /**
     * Posts the date a mission is announced for.
     *
     * The whole drawing is read again afterwards rather than the one line
     * patched: moving a date moves nothing else, but the tally above it does,
     * and a screen whose bars and tally disagree is worse than one that waits
     * a moment.
     *
     * A refusal is caught and said out loud. Letting it through would leave
     * the row showing a date the server never took, which is the one thing a
     * screen about commitments must not do.
     */
    async setTargetDate(projectId: number, target: string | null) {
      try {
        await updateProject(projectId, { go_live_date: target });
        setSaveFailed(false);
      } catch {
        setSaveFailed(true);
      }
      await fetchReading(reading);
    },
  };
}
