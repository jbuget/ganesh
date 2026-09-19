import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useMissionColumns } from "./use-mission-columns";
import { useMissionSort } from "./use-mission-sort";

beforeEach(() => {
  window.history.replaceState(null, "", "/projets");
});

/** The order is read from the address too: a bare one orders nothing. */
function columns() {
  return renderHook(() => {
    const { sorted } = useMissionSort();
    return useMissionColumns(sorted);
  });
}

describe("useMissionColumns", () => {
  it("shows the whole panorama to start with", () => {
    const { result } = columns();

    expect(result.current.hidden.size).toBe(0);
    expect(result.current.isVisible("category")).toBe(true);
  });

  it("puts away the column asked for, and says so in the address", () => {
    const { result } = columns();

    act(() => result.current.toggle("category"));

    expect(result.current.isVisible("category")).toBe(false);
    expect(window.location.search).toContain("hide=category");
  });

  it("brings back a column put away", () => {
    const { result } = columns();

    act(() => result.current.toggle("category"));
    act(() => result.current.toggle("category"));

    expect(result.current.isVisible("category")).toBe(true);
    expect(window.location.search).toBe("");
  });

  it("narrows the table by what the column put away was taking", () => {
    const { result } = columns();
    const whole = result.current.width;

    act(() => result.current.toggle("category"));

    expect(result.current.width).toBeLessThan(whole);
  });

  it("brings the whole panorama back at once", () => {
    const { result } = columns();

    act(() => result.current.toggle("category"));
    act(() => result.current.toggle("published"));
    act(() => result.current.showAll());

    expect(result.current.hidden.size).toBe(0);
    expect(window.location.search).toBe("");
  });

  it("adds no history step: choosing columns is not navigating", () => {
    const depth = window.history.length;
    const { result } = columns();

    act(() => result.current.toggle("category"));
    act(() => result.current.toggle("published"));

    expect(window.history.length).toBe(depth);
  });
});

/**
 * An order is read off the column that carries it. Put that column away and
 * the list keeps an order nothing on screen explains any more.
 */
describe("living alongside the sort", () => {
  it("gives the list its own order back when the column it is sorted by goes", () => {
    const { result } = renderHook(() => {
      const sort = useMissionSort();
      return { sort, columns: useMissionColumns(sort.sorted) };
    });

    act(() => result.current.sort.toggle("category"));
    act(() => result.current.columns.toggle("category"));

    expect(result.current.sort.sorted.column).toBeNull();
    expect(window.location.search).not.toContain("sort=");
  });

  it("leaves an order carried by another column alone", () => {
    const { result } = renderHook(() => {
      const sort = useMissionSort();
      return { sort, columns: useMissionColumns(sort.sorted) };
    });

    act(() => result.current.sort.toggle("build"));
    act(() => result.current.columns.toggle("category"));

    expect(result.current.sort.sorted.column).toBe("build");
  });

  /** The name column never goes away, so the order it carries never does. */
  it("leaves an order carried by the name alone", () => {
    const { result } = renderHook(() => {
      const sort = useMissionSort();
      return { sort, columns: useMissionColumns(sort.sorted) };
    });

    act(() => result.current.sort.toggle("project"));
    act(() => result.current.columns.toggle("category"));

    expect(result.current.sort.sorted.column).toBe("project");
  });
});
