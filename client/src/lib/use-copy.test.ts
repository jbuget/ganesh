import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useCopy } from "@/lib/use-copy";

let writeText: ReturnType<typeof vi.fn>;

beforeEach(() => {
  writeText = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, { clipboard: { writeText } });
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

/** Runs the gesture and lets the clipboard's promise settle. */
async function copyWith(result: { current: ReturnType<typeof useCopy> }) {
  await act(async () => {
    result.current.copy();
    await vi.advanceTimersByTimeAsync(0);
  });
}

describe("useCopy", () => {
  it("offers the gesture before anything is asked of it", () => {
    const { result } = renderHook(() => useCopy("jns_abcdef"));
    expect(result.current.copied).toBe(false);
  });

  it("hands the value to the clipboard", async () => {
    const { result } = renderHook(() => useCopy("jns_abcdef"));

    await copyWith(result);

    expect(writeText).toHaveBeenCalledWith("jns_abcdef");
  });

  it("reports the copy, long enough to be seen", async () => {
    const { result } = renderHook(() => useCopy("jns_abcdef"));

    await copyWith(result);

    expect(result.current.copied).toBe(true);
  });

  it("goes back to offering the gesture rather than reporting the past", async () => {
    // A button left saying « Copiée » reports the past: the next reader cannot
    // tell whether it is offering the gesture or remembering somebody else's.
    const { result } = renderHook(() => useCopy("jns_abcdef"));

    await copyWith(result);
    await act(() => vi.advanceTimersByTimeAsync(2000));

    expect(result.current.copied).toBe(false);
  });

  it("says nothing was copied when the clipboard refuses", async () => {
    // A browser may deny the clipboard outright. Saying « Copié » anyway is
    // the one answer that loses the value: nobody copies it a second time.
    writeText.mockRejectedValue(new Error("refusé"));
    const { result } = renderHook(() => useCopy("jns_abcdef"));

    await copyWith(result);

    expect(result.current.copied).toBe(false);
  });
});
