"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/** What was about to be done, held back until someone says it is all right. */
interface HeldBack {
  run: () => void;
}

/**
 * Stands between unsaved work and whatever would throw it away.
 *
 * Two exits, and they cannot be guarded the same way. Leaving the application
 * — reloading, closing the tab, typing another address — is the browser's to
 * refuse, and `beforeunload` is the only say we get: the wording is the
 * browser's own and cannot be ours. Moving inside the application never
 * unloads anything, so the click has to be caught before the router acts on
 * it, and there we can ask the question in our own words.
 *
 * The interceptor runs in the capture phase, ahead of the router's own
 * handler, and only on a plain left click on a same-origin link: a middle
 * click, a ⌘-click or a download opens elsewhere and takes nothing away.
 */
export function useUnsavedChangesGuard(isDirty: boolean) {
  const router = useRouter();
  const [heldBack, setHeldBack] = useState<HeldBack | null>(null);

  useEffect(() => {
    if (!isDirty) return;

    const warn = (event: BeforeUnloadEvent) => {
      // Both: `preventDefault` is what the standard asks for today, and
      // `returnValue` is what the older engines still read.
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [isDirty]);

  useEffect(() => {
    if (!isDirty) return;

    const intercept = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const anchor = (event.target as HTMLElement | null)?.closest?.("a");
      if (!anchor) return;

      const href = anchor.getAttribute("href");
      if (!href || href.startsWith("#")) return;
      if (anchor.target && anchor.target !== "_self") return;
      if (anchor.hasAttribute("download")) return;

      const target = new URL(anchor.href, window.location.href);
      if (target.origin !== window.location.origin) return;
      // Staying where one is takes nothing away.
      if (target.pathname === window.location.pathname) return;

      event.preventDefault();
      const to = `${target.pathname}${target.search}`;
      setHeldBack({ run: () => router.push(to) });
    };

    document.addEventListener("click", intercept, true);
    return () => document.removeEventListener("click", intercept, true);
  }, [isDirty, router]);

  return {
    /** Whether something is waiting on an answer. */
    isBlocking: heldBack !== null,
    /** Stays put, and forgets what was asked for. */
    stay: () => setHeldBack(null),
    /** Goes ahead and loses the work. */
    discard: () => {
      heldBack?.run();
      setHeldBack(null);
    },
    /**
     * Wraps an action that would throw the work away.
     *
     * Opening another simulation loses exactly what leaving the page loses:
     * the question is worth asking in both cases, and asking it the same way
     * twice is what makes it read as a rule rather than a quirk.
     */
    guard:
      <T extends unknown[]>(run: (...args: T) => void) =>
      (...args: T) => {
        if (isDirty) setHeldBack({ run: () => run(...args) });
        else run(...args);
      },
  };
}
