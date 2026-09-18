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

interface DeclareProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (label: string) => Promise<void>;
  /** The same dialog declares a project or adds a sub-project to one. */
  title?: string;
}

/** Declaring a new project, open to the whole team. */
export function DeclareProjectDialog({
  open,
  onOpenChange,
  onConfirm,
  title = "Déclarer un projet",
}: DeclareProjectDialogProps) {
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);

  const isValid = label.trim().length > 0;

  async function confirm() {
    if (!isValid) return;
    setBusy(true);
    try {
      await onConfirm(label.trim());
      setLabel("");
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            Le projet sera ajouté au référentiel commun et visible de toute
            l&apos;équipe.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="project-label">Nom du projet</Label>
          <Input
            id="project-label"
            value={label}
            autoFocus
            placeholder="Refonte extranet copropriété"
            onChange={(event) => setLabel(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") confirm();
            }}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={confirm} disabled={!isValid || busy}>
            Déclarer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
