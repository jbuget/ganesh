import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useUnsavedChangesGuard } from "./use-unsaved-changes-guard";

const pushed = vi.hoisted(() => ({ to: null as string | null }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: (to: string) => {
      pushed.to = to;
    },
  }),
}));

/** A link in the page, as the sidebar draws one. */
function aLink(href: string, attributes: Record<string, string> = {}) {
  const anchor = document.createElement("a");
  anchor.setAttribute("href", href);
  for (const [name, value] of Object.entries(attributes)) {
    anchor.setAttribute(name, value);
  }
  document.body.append(anchor);
  return anchor;
}

function clickOn(anchor: HTMLAnchorElement, init: MouseEventInit = {}) {
  const event = new MouseEvent("click", {
    bubbles: true,
    cancelable: true,
    button: 0,
    ...init,
  });
  // Held back inside `act`: catching the click sets state, and React wants
  // that settled before anything is asserted.
  act(() => {
    anchor.dispatchEvent(event);
  });
  return event;
}

beforeEach(() => {
  document.body.innerHTML = "";
  pushed.to = null;
  window.history.replaceState(null, "", "/planning");
});

describe("useUnsavedChangesGuard", () => {
  describe("moving inside the application", () => {
    it("holds a link back while there is work to lose", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(true));

      const event = clickOn(aLink("/kanban"));

      expect(event.defaultPrevented).toBe(true);
      expect(result.current.isBlocking).toBe(true);
      expect(pushed.to).toBeNull();
    });

    it("lets a link through once there is nothing to lose", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(false));

      const event = clickOn(aLink("/kanban"));

      expect(event.defaultPrevented).toBe(false);
      expect(result.current.isBlocking).toBe(false);
    });

    it("goes where one was going once the work is given up", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(true));
      clickOn(aLink("/kanban?phase=development"));

      act(() => result.current.discard());

      expect(pushed.to).toBe("/kanban?phase=development");
      expect(result.current.isBlocking).toBe(false);
    });

    it("stays put, and forgets where one was going", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(true));
      clickOn(aLink("/kanban"));

      act(() => result.current.stay());

      expect(pushed.to).toBeNull();
      expect(result.current.isBlocking).toBe(false);
    });

    it("leaves alone a click that opens somewhere else", () => {
      // A ⌘-click, a middle click or a new tab takes nothing away.
      const { result } = renderHook(() => useUnsavedChangesGuard(true));

      clickOn(aLink("/kanban"), { metaKey: true });
      clickOn(aLink("/kanban"), { button: 1 });
      clickOn(aLink("/kanban", { target: "_blank" }));

      expect(result.current.isBlocking).toBe(false);
    });

    it("leaves alone a link off the application", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(true));

      clickOn(aLink("https://monday.com/board/1"));

      expect(result.current.isBlocking).toBe(false);
    });

    it("leaves alone a link going nowhere", () => {
      // An anchor within the page, or the page one is already on.
      const { result } = renderHook(() => useUnsavedChangesGuard(true));

      clickOn(aLink("#section"));
      clickOn(aLink("/planning"));

      expect(result.current.isBlocking).toBe(false);
    });

    it("leaves alone a download", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(true));

      clickOn(aLink("/export.csv", { download: "" }));

      expect(result.current.isBlocking).toBe(false);
    });
  });

  describe("leaving the application", () => {
    it("asks the browser to warn while there is work to lose", () => {
      renderHook(() => useUnsavedChangesGuard(true));

      const event = new Event("beforeunload", { cancelable: true });
      window.dispatchEvent(event);

      expect(event.defaultPrevented).toBe(true);
    });

    it("says nothing once there is nothing to lose", () => {
      renderHook(() => useUnsavedChangesGuard(false));

      const event = new Event("beforeunload", { cancelable: true });
      window.dispatchEvent(event);

      expect(event.defaultPrevented).toBe(false);
    });

    it("stops warning as soon as the work is saved", () => {
      const { rerender } = renderHook(({ dirty }) => useUnsavedChangesGuard(dirty), {
        initialProps: { dirty: true },
      });

      rerender({ dirty: false });

      const event = new Event("beforeunload", { cancelable: true });
      window.dispatchEvent(event);

      expect(event.defaultPrevented).toBe(false);
    });
  });

  describe("guarding an action in the page", () => {
    it("holds back what would throw the work away", () => {
      // Opening another simulation loses exactly what leaving the page loses.
      const { result } = renderHook(() => useUnsavedChangesGuard(true));
      const open = vi.fn();

      act(() => result.current.guard(open)(7));

      expect(open).not.toHaveBeenCalled();
      expect(result.current.isBlocking).toBe(true);
    });

    it("runs it with what it was given once the work is given up", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(true));
      const open = vi.fn();
      act(() => result.current.guard(open)(7));

      act(() => result.current.discard());

      expect(open).toHaveBeenCalledWith(7);
    });

    it("lets it through while there is nothing to lose", () => {
      const { result } = renderHook(() => useUnsavedChangesGuard(false));
      const open = vi.fn();

      act(() => result.current.guard(open)(7));

      expect(open).toHaveBeenCalledWith(7);
      expect(result.current.isBlocking).toBe(false);
    });
  });
});
