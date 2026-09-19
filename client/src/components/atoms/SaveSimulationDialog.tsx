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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface SaveSimulationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Returns false when the name is already taken, keeping the dialog open. */
  onConfirm: (name: string) => Promise<boolean>;
  /** What the server refused, if it refused something. */
  error: string | null;
}

/**
 * Naming a scenario so it survives the session.
 *
 * What is kept is the question, never the answer: a landing date frozen in a
 * row would be a lie by the following Monday, so a reopened simulation is
 * projected again against whatever has been declared since.
 */
export function SaveSimulationDialog({
  open,
  onOpenChange,
  onConfirm,
  error,
}: SaveSimulationDialogProps) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  const isValid = name.trim().length > 0;

  async function confirm() {
    if (!isValid || busy) return;
    setBusy(true);
    try {
      // A refused name leaves the dialog open on what was typed: retyping the
      // whole thing to change one word is a punishment, not a correction.
      if (await onConfirm(name.trim())) {
        setName("");
        onOpenChange(false);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enregistrer la simulation</DialogTitle>
          <DialogDescription>
            L&apos;hypothèse est conservée, pas ses dates : à la réouverture, elle est
            reprojetée sur les disponibilités du moment.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="simulation-name">Nom de la simulation</Label>
          <Input
            id="simulation-name"
            value={name}
            autoFocus
            placeholder="Priorité bailleurs, Valentin sur le portail"
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void confirm();
            }}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            className="cursor-pointer"
            onClick={() => onOpenChange(false)}
          >
            Annuler
          </Button>
          <Button
            className="cursor-pointer"
            onClick={() => void confirm()}
            disabled={!isValid || busy}
          >
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
