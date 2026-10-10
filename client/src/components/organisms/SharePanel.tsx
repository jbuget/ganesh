"use client";

import { Link2 } from "lucide-react";

import { ShareLinkRow } from "@/components/atoms/ShareLinkRow";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { formatGeneratedAt } from "@/lib/gazette";
import { useShare } from "@/lib/use-share-links";

interface SharePanelProps {
  month: string;
  /** The version on screen: a link names one, never the month. */
  version: number;
}

/**
 * Putting the version on screen behind a link.
 *
 * Whoever holds a link reads the narrative of that version, without signing
 * in, and can do nothing else. The panel says so before it asks for anything,
 * and lists every link still open for the whole team: with no date a link
 * lapses on, that list is how one left in a mail from last year is found.
 */
export function SharePanel({ month, version }: SharePanelProps) {
  const share = useShare(month, version);

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button variant="outline" className="cursor-pointer">
            <Link2 /> Partager
          </Button>
        }
      />
      <PopoverContent align="end" className="w-[26rem]">
        <p className="text-sm font-medium text-slate-900">
          Partager la version {version}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Toute personne qui a le lien lit le récit de cette version, sans se connecter,
          et ne peut rien faire d&apos;autre. Le lien reste ouvert jusqu&apos;à ce que
          quelqu&apos;un le ferme.
        </p>

        {share.links.length > 0 && (
          <ul className="mt-2 divide-y divide-slate-100">
            {share.links.map((link) => (
              <ShareLinkRow
                key={link.id}
                address={share.addressOf(link.token)}
                openedBy={`Ouvert par ${link.created_by ?? "un ancien membre"} le ${formatGeneratedAt(link.created_at)}`}
                onCopy={() =>
                  navigator.clipboard.writeText(share.addressOf(link.token))
                }
                onClose={() => void share.close(link.id)}
              />
            ))}
          </ul>
        )}

        <Button
          className="mt-2 w-full cursor-pointer"
          disabled={share.isOpening}
          onClick={() => void share.open()}
        >
          {share.isOpening ? "Création…" : "Créer un lien"}
        </Button>
      </PopoverContent>
    </Popover>
  );
}
