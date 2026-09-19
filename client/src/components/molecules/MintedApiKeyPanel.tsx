"use client";

import { TriangleAlert } from "lucide-react";

import { CopyableSecret } from "@/components/atoms/CopyableSecret";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { MintedApiKeyResponse } from "@/lib/api/generated/model";

interface MintedApiKeyPanelProps {
  minted: MintedApiKeyResponse | null;
  onClose: () => void;
}

/**
 * The single most important screen of the feature.
 *
 * Everything else here is recoverable; this is not. The token exists in this
 * panel and nowhere else — nothing stored it, no route hands it over again —
 * so closing loses it for good. The wording says so before the gesture, not
 * after.
 */
export function MintedApiKeyPanel({ minted, onClose }: MintedApiKeyPanelProps) {
  if (minted === null) return null;

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Clé « {minted.key.name} » créée</DialogTitle>
          <DialogDescription>
            Copiez-la maintenant et rangez-la dans le coffre du service qui
            l&apos;utilisera.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2.5 text-sm text-amber-900">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            Cette clé ne sera plus jamais affichée. Ganesh n&apos;en conserve
            qu&apos;une empreinte : si elle est perdue, il faudra en créer une autre.
          </p>
        </div>

        <CopyableSecret value={minted.token} />

        <DialogFooter>
          <Button className="cursor-pointer" onClick={onClose}>
            J&apos;ai copié la clé
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
