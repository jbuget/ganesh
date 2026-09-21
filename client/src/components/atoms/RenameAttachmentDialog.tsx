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

interface RenameAttachmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The name it carries now; the field opens on it. */
  filename: string;
  onConfirm: (filename: string) => void | Promise<void>;
}

/**
 * Calling a file something else.
 *
 * The field opens on the whole current name, extension included: changing
 * « capture.png » into « bug de mars.png » is a word to retype, and dropping
 * the suffix takes doing it on purpose. Nothing is put back afterwards — a
 * name is what somebody typed.
 */
export function RenameAttachmentDialog({
  open,
  onOpenChange,
  filename,
  onConfirm,
}: RenameAttachmentDialogProps) {
  const [chosen, setChosen] = useState(filename);
  const [busy, setBusy] = useState(false);

  const unchanged = chosen.trim() === filename || !chosen.trim();

  async function confirm() {
    if (unchanged) return;
    setBusy(true);
    try {
      await onConfirm(chosen.trim());
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Renommer le fichier</DialogTitle>
          <DialogDescription>
            Le fichier reste le même : seul le nom sous lequel on le lit change.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="attachment-filename">Nom du fichier</Label>
          <Input
            id="attachment-filename"
            value={chosen}
            autoFocus
            onChange={(event) => setChosen(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void confirm();
            }}
          />
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            className="cursor-pointer"
            onClick={() => onOpenChange(false)}
          >
            Annuler
          </Button>
          <Button
            className="cursor-pointer"
            disabled={unchanged || busy}
            onClick={() => void confirm()}
          >
            Renommer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
