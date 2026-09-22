import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const back = vi.fn();
const pathname = { value: "/kanban" };

vi.mock("next/navigation", () => ({
  usePathname: () => pathname.value,
  useRouter: () => ({ back }),
}));

import { forgetTrail, useNavigationTrail, useWayBack } from "./navigation-trail";

const REFERENCE_LIST = { href: "/projects", label: "Projets" };

/** Crosses the screens, as the sidebar does above every one of them. */
function landOn(screen: string) {
  pathname.value = screen;
  const trail = renderHook(() => useNavigationTrail());

  return {
    then(next: string) {
      pathname.value = next;
      trail.rerender();
      return this;
    },
  };
}

beforeEach(() => {
  // A load starts the trail afresh; jsdom never loads anything.
  forgetTrail();
  back.mockClear();
});

describe("useWayBack", () => {
  it("names where it goes when nothing was left behind", () => {
    // Landed straight on the sheet — a link shared, a new tab: the browser has
    // nothing of ours behind it.
    landOn("/projects/12");

    const { result } = renderHook(() => useWayBack(REFERENCE_LIST));

    expect(result.current).toEqual({ label: "Projets", href: "/projects" });
  });

  it("walks the browser back to the screen one came from", () => {
    landOn("/kanban").then("/projects/12");

    const { result } = renderHook(() => useWayBack(REFERENCE_LIST));

    expect(result.current.label).toBe("Retour");
    // No address to name: the browser alone knows where it lands.
    expect(result.current.href).toBeUndefined();

    act(() => result.current.back?.());

    expect(back).toHaveBeenCalled();
  });

  it("hears the arrival recorded after the screen has drawn itself", () => {
    // The order of a real navigation: the sheet renders, and only then does
    // the bar above it record the arrival. Without a word to those already
    // rendered, the sheet would keep the answer meant for the screen left.
    const trail = landOn("/kanban");
    const { result } = renderHook(() => useWayBack(REFERENCE_LIST));

    expect(result.current.label).toBe("Projets");

    act(() => {
      trail.then("/projects/12");
    });

    expect(result.current.label).toBe("Retour");
  });

  it("does not take a screen rendered again for a screen left", () => {
    // The address is written to without moving — a filter set, a panel opened.
    landOn("/projects/12").then("/projects/12");

    const { result } = renderHook(() => useWayBack(REFERENCE_LIST));

    expect(result.current.label).toBe("Projets");
  });

  it("still goes back one step from a sheet reached through another", () => {
    // The project a work package belongs to, opened from the package's sheet.
    landOn("/kanban").then("/projects/12").then("/projects/31");

    const { result } = renderHook(() => useWayBack(REFERENCE_LIST));

    expect(result.current.label).toBe("Retour");
  });
});
