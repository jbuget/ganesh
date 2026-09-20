"use client";

import { useState } from "react";

/** How long the button reports the copy before offering the gesture again. */
const SEEN = 2000;

/**
 * Copying to the clipboard, and the moment of proof that follows.
 *
 * Both things that get copied in the application — a token shown once, a
 * configuration snippet — need the same two beats: the write, then a button
 * that says « done » for long enough to be seen and then goes back to
 * offering the gesture. Written twice, the two drift on the delay alone, and
 * one of them starts reporting the past for good.
 */
export function useCopy(value: string): { copied: boolean; copy: () => void } {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard
      .writeText(value)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), SEEN);
      })
      // A browser may deny the clipboard outright. Saying « Copié » anyway is
      // the one answer that loses the value: the button would report a copy
      // nobody made, and nobody copies it a second time.
      .catch(() => setCopied(false));
  }

  return { copied, copy };
}
