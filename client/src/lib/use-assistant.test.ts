import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { ApiError } from "@/lib/api/fetcher";
import type { ExchangeResponse } from "@/lib/api/generated/model";

import { useAssistant } from "./use-assistant";

const api = vi.hoisted(() => ({ askAssistant: vi.fn(), judgeAnswer: vi.fn() }));
const where = vi.hoisted(() => ({ pathname: "/timesheet" }));
const cache = vi.hoisted(() => ({ invalidateQueries: vi.fn() }));

vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => cache }));

vi.mock("@/lib/api/generated/assistant/assistant", () => api);
vi.mock("next/navigation", () => ({ usePathname: () => where.pathname }));
vi.mock("@/lib/api/queries", () => ({
  mutationResult: (response: { data: unknown }) => response.data,
  useAssistantStatus: () => ({ status: { is_available: true, max_exchanges: 5 } }),
  useProjects: () => ({
    missions: [{ project: { id: 7, label: "WAATcher", kind: "project" } }],
  }),
  useTeammates: () => ({
    teammates: [
      { id: 3, display_name: "David DEHE", first_name: null, last_name: null },
    ],
  }),
}));

function an_exchange(fields: Partial<ExchangeResponse> = {}): ExchangeResponse {
  return {
    id: 1,
    conversation_id: "c0nv",
    rank: 1,
    remaining: 4,
    question: "Où en est WAATcher ?",
    answer: "En développement.",
    consulted_project_ids: [7],
    verdict: null,
    ...fields,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  where.pathname = "/timesheet";
  api.askAssistant.mockResolvedValue({ data: an_exchange() });
  api.judgeAnswer.mockResolvedValue({ data: undefined });
});

describe("useAssistant", () => {
  it("opens a conversation on the first question", async () => {
    const { result } = renderHook(() => useAssistant());

    await act(() => result.current.ask("Où en est WAATcher ?"));

    expect(api.askAssistant).toHaveBeenCalledWith({
      question: "Où en est WAATcher ?",
      conversation_id: null,
      project_id: null,
    });
    expect(result.current.turns).toEqual([
      {
        id: 1,
        question: "Où en est WAATcher ?",
        answer: "En développement.",
        consulted: [{ id: 7, label: "WAATcher" }],
        verdict: null,
      },
    ]);
    expect(result.current.remaining).toBe(4);
  });

  it("knows where the projects and the people an answer names lead", async () => {
    api.askAssistant.mockResolvedValue({
      data: an_exchange({ answer: "WAATcher est porté par David DEHE." }),
    });
    const { result } = renderHook(() => useAssistant());

    await act(() => result.current.ask("Qui porte WAATcher ?"));

    expect(result.current.turns[0].answer).toBe("WAATcher est porté par David DEHE.");
    expect(result.current.names.get("WAATcher")).toBe("/projects/7");
    expect(result.current.names.get("David DEHE")).toBe("/users?user=3");
  });

  it("says how many questions a conversation holds, as the server does", () => {
    const { result } = renderHook(() => useAssistant());

    expect(result.current.maxExchanges).toBe(5);
  });

  it("carries the conversation on with the next question", async () => {
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));

    await act(() => result.current.ask("Et depuis ?"));

    expect(api.askAssistant).toHaveBeenLastCalledWith(
      expect.objectContaining({ conversation_id: "c0nv" }),
    );
  });

  it("asks about the project whose page is open", async () => {
    where.pathname = "/projects/7";
    const { result } = renderHook(() => useAssistant());

    await act(() => result.current.ask("Où en est-il ?"));

    expect(api.askAssistant).toHaveBeenCalledWith(
      expect.objectContaining({ project_id: 7 }),
    );
  });

  it("says why a question went unanswered", async () => {
    api.askAssistant.mockRejectedValue(new ApiError(503, "No model"));
    const { result } = renderHook(() => useAssistant());

    await act(() => result.current.ask("Où en est WAATcher ?"));

    expect(result.current.refusal).toBe(
      "L'assistant est indisponible pour le moment. Réessayez plus tard.",
    );
    expect(result.current.turns).toEqual([]);
    expect(result.current.pending).toBeNull();
  });

  it("is over once the conversation has had its exchanges", async () => {
    api.askAssistant.mockResolvedValue({
      data: an_exchange({ rank: 5, remaining: 0 }),
    });
    const { result } = renderHook(() => useAssistant());

    await act(() => result.current.ask("Dernière ?"));

    expect(result.current.isOver).toBe(true);
  });

  it("starts afresh, the next question opening a new conversation", async () => {
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));

    act(() => result.current.restart());
    await act(() => result.current.ask("Autre chose ?"));

    expect(result.current.remaining).toBe(4);
    expect(api.askAssistant).toHaveBeenLastCalledWith(
      expect.objectContaining({ conversation_id: null }),
    );
  });

  it("keeps the verdict given on an answer", async () => {
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));

    await act(() => result.current.judge(1, "helpful"));

    expect(api.judgeAnswer).toHaveBeenCalledWith(1, { verdict: "helpful" });
    expect(result.current.turns[0].verdict).toBe("helpful");
  });

  it("reads the administration's study again once a verdict is kept", async () => {
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));
    cache.invalidateQueries.mockClear();

    await act(() => result.current.judge(1, "helpful"));

    expect(cache.invalidateQueries).toHaveBeenCalledTimes(1);
  });

  it("leaves the study alone when the verdict was not kept", async () => {
    api.judgeAnswer.mockRejectedValue(new Error("network"));
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));
    cache.invalidateQueries.mockClear();

    await act(() => result.current.judge(1, "helpful"));

    expect(cache.invalidateQueries).not.toHaveBeenCalled();
  });

  it("shows the verdict before the server has kept it", async () => {
    let keep: () => void = () => {};
    api.judgeAnswer.mockReturnValue(new Promise<void>((resolve) => (keep = resolve)));
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));

    let judging: Promise<void> = Promise.resolve();
    act(() => {
      judging = result.current.judge(1, "unhelpful");
    });

    expect(result.current.turns[0].verdict).toBe("unhelpful");
    await act(async () => {
      keep();
      await judging;
    });
  });

  it("takes the verdict back when the server did not keep it", async () => {
    api.judgeAnswer.mockRejectedValue(new Error("network"));
    const { result } = renderHook(() => useAssistant());
    await act(() => result.current.ask("Où en est WAATcher ?"));

    await act(() => result.current.judge(1, "helpful"));

    expect(result.current.turns[0].verdict).toBeNull();
  });
});
