"use client";

import { useEffect } from "react";

interface SidePanelProps {
  /** What the panel holds, for whoever navigates by landmarks. */
  label: string;
  onClose: () => void;
  children: React.ReactNode;
}

/**
 * A panel sliding in from the right, over the screen it was opened from.
 *
 * The screen behind stays visible and readable: one looks at one row without
 * losing sight of the list it comes from. Escape and the veil both close it —
 * a panel must never be a place one gets stuck in.
 */
export function SidePanel({ label, onClose, children }: SidePanelProps) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  return (
    <>
      {/*
        The veil closes on click but does not hide: what lies behind must stay
        readable, which is the whole point of a panel rather than a page.
      */}
      <div
        aria-hidden
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-900/5"
      />

      <aside
        aria-label={label}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[40rem] flex-col border-l border-slate-300 bg-white shadow-xl"
      >
        {children}
      </aside>
    </>
  );
}
