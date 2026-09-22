"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { RequestState } from "@/lib/api/generated/model";

interface DecideRequestDialogProps {
  /** Null when no decision is being taken: the dialog is then shut. */
  decision: RequestState | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: (note: string | null) => Promise<void>;
}

/** What each decision is called, and what it asks for before it is taken. */
const DECISIONS: Record<string, { title: string; ask: string; demanded: boolean }> = {
  accepted: {
    title: "Accepter la demande",
    ask: "Un mot sur la décision, si vous le souhaitez.",
    demanded: false,
  },
  rejected: {
    title: "Refuser la demande",
    ask: "Pourquoi cette demande n'est pas retenue.",
    demanded: true,
  },
  deferred: {
    title: "Reporter la demande",
    ask: "Pourquoi ce n'est pas le moment, et ce qu'il faudrait pour que ça le devienne.",
    demanded: true,
  },
};

/**
 * Taking a decision, and saying why.
 *
 * A refusal and a « plus tard » are refused without a motive — the domain says
 * so, and this asks for it where the decision is taken. A « non » with no
 * reason attached comes back word for word three months later.
 */
export function DecideRequestDialog({
  decision,
  onOpenChange,
  onConfirm,
}: DecideRequestDialogProps) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const wording = decision ? DECISIONS[decision] : null;

  const isValid = !wording?.demanded || note.trim().length > 0;

  async function confirm() {
    if (!isValid) return;
    setBusy(true);
    try {
      await onConfirm(note.trim() || null);
      setNote("");
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={decision !== null}
      onOpenChange={(next) => {
        if (!next) setNote("");
        onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{wording?.title ?? "Arbitrer la demande"}</DialogTitle>
          <DialogDescription>{wording?.ask}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="decision-note">
            Motif{wording?.demanded ? "" : " (facultatif)"}
          </Label>
          <Textarea
            id="decision-note"
            rows={4}
            value={note}
            autoFocus
            onChange={(event) => setNote(event.target.value)}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={() => void confirm()} disabled={!isValid || busy}>
            Confirmer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
