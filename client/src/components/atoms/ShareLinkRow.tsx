"use client";

import { Check, Copy, Link2Off } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

interface ShareLinkRowProps {
  /** Where the link is read, in full: what gets pasted into a mail. */
  address: string;
  /** Who opened it, and when, said in French. Nobody once they are gone. */
  openedBy: string;
  onCopy: () => Promise<void> | void;
  onClose: () => void;
}

/**
 * One open link: its address, who made it, a way to copy it and a way to
 * close it.
 *
 * With no date a link lapses on, closing is the only way one ends, so the
 * button is there on every line rather than behind a menu.
 */
export function ShareLinkRow({
  address,
  openedBy,
  onCopy,
  onClose,
}: ShareLinkRowProps) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await onCopy();
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <li className="flex flex-col gap-1 py-2">
      <div className="flex items-center gap-1.5">
        <input
          readOnly
          value={address}
          aria-label="Adresse du lien"
          onFocus={(event) => event.currentTarget.select()}
          className="min-w-0 flex-1 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="cursor-pointer"
          aria-label={copied ? "Lien copié" : "Copier le lien"}
          onClick={() => void copy()}
        >
          {copied ? <Check /> : <Copy />}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="cursor-pointer"
          aria-label="Fermer le lien"
          onClick={onClose}
        >
          <Link2Off />
        </Button>
      </div>
      <p className="text-xs text-slate-500">{openedBy}</p>
    </li>
  );
}
