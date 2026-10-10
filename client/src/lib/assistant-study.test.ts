import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import {
  CAUSES,
  NO_STUDY_FILTER,
  asStudyQuery,
  causeLabel,
  hasStudyFilter,
  refreshStudy,
  seconds,
  share,
  WHY_UNANSWERED,
  whyUnansweredLabel,
} from "@/lib/assistant-study";

describe("the criteria of the study", () => {
  it("leaves out every criterion nobody set", () => {
    expect(asStudyQuery(NO_STUDY_FILTER)).toEqual({});
    expect(hasStudyFilter(NO_STUDY_FILTER)).toBe(false);
  });

  it("asks for one person, a judgement and a period in days", () => {
    const filters = {
      askerIds: ["4"],
      judgement: "unhelpful" as const,
      fromDay: "2026-10-01",
      toDay: "2026-10-10",
    };

    expect(asStudyQuery(filters)).toEqual({
      asker_id: 4,
      judgement: "unhelpful",
      from_day: "2026-10-01",
      to_day: "2026-10-10",
    });
    expect(hasStudyFilter(filters)).toBe(true);
  });
});

describe("what a cause is called", () => {
  it("names every cause the API knows, in French", () => {
    expect(CAUSES.map((cause) => cause.value)).toEqual([
      "wrong_reading",
      "wrong_phrasing",
      "out_of_scope",
      "right_answer",
    ]);
    expect(causeLabel("wrong_reading")).toBe("Lecture fausse");
  });
});

describe("why a question went unanswered", () => {
  it("names every reason the API knows, in French", () => {
    expect(WHY_UNANSWERED.map((held) => held.value)).toEqual([
      "provider_failed",
      "cut_short",
      "kept_asking",
    ]);
    expect(whyUnansweredLabel("kept_asking")).toBe("Lectures sans fin");
  });
});

describe("the figures", () => {
  it("says a wait in seconds, the French way", () => {
    expect(seconds(5230)).toBe("5,2 s");
    expect(seconds(null)).toBe("—");
  });

  it("says a share as a whole percentage, and nothing of nothing", () => {
    expect(share(1, 3)).toBe("33 %");
    expect(share(0, 0)).toBe("—");
  });
});

describe("reading the study again", () => {
  it("marks every reading of the study stale, and nothing else", async () => {
    const queryClient = new QueryClient();
    const keys = [
      ["/api/v1/admin/assistant/conversations", { limit: 50 }],
      ["/api/v1/admin/assistant/conversations/c0nv"],
      ["/api/v1/admin/assistant/indicators", {}],
      ["/api/v1/admin/platform"],
      ["/api/v1/assistant"],
    ];
    for (const key of keys) queryClient.setQueryData(key, {});

    await refreshStudy(queryClient);

    expect(keys.map((key) => queryClient.getQueryState(key)?.isInvalidated)).toEqual([
      true,
      true,
      true,
      false,
      false,
    ]);
  });
});
