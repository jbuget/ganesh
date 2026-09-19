"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

/**
 * A secret shown once, with the one gesture that saves it.
 *
 * Reading a forty-character token off a screen is not a plan: the button is
 * the feature, the text beside it is only proof of what was copied.
 */
export function CopyableSecret({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    // Long enough to be seen, short enough that the button goes back to
    // offering the gesture rather than reporting the past.
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    // `min-w-0`: the dialog lays its children out in a grid, where a track is
    // `min-width: auto` and refuses to shrink under its content. Without it the
    // token pushes the panel past its own edge and `truncate` never applies.
    <div className="flex min-w-0 items-center gap-2">
      <code className="min-w-0 flex-1 truncate rounded border border-slate-300 bg-white px-2 py-1.5 font-mono text-sm text-slate-800">
        {value}
      </code>
      <Button
        size="sm"
        variant="outline"
        className="cursor-pointer"
        onClick={() => void copy()}
      >
        {copied ? (
          <>
            <Check className="size-3.5" aria-hidden />
            Copiée
          </>
        ) : (
          <>
            <Copy className="size-3.5" aria-hidden />
            Copier
          </>
        )}
      </Button>
    </div>
  );
}
