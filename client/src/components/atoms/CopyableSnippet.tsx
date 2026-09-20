"use client";

import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCopy } from "@/lib/use-copy";

interface CopyableSnippetProps {
  /** The lines to show, verbatim. Never truncated: they are meant to be read. */
  value: string;
  /** What the button announces to a screen reader. */
  label: string;
}

/**
 * A block of configuration, with the one gesture that moves it.
 *
 * `CopyableSecret` is its one-line cousin, and stays one: a token is proof of
 * what was copied and truncates safely, whereas a snippet is read before it is
 * pasted — a JSON object cut off at the edge of its box would be copied wrong
 * and debugged for an hour.
 */
export function CopyableSnippet({ value, label }: CopyableSnippetProps) {
  const { copied, copy } = useCopy(value);

  return (
    <div className="relative">
      <pre className="overflow-x-auto rounded-md border border-slate-300 bg-slate-900 px-3 py-2.5 pr-24 font-mono text-xs leading-relaxed text-slate-100">
        {value}
      </pre>

      <Button
        size="sm"
        variant="outline"
        aria-label={label}
        className="absolute top-2 right-2 cursor-pointer"
        onClick={copy}
      >
        {copied ? (
          <>
            <Check className="size-3.5" aria-hidden />
            Copié
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
