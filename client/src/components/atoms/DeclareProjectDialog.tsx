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
  titre?: string;
}

/** Declaring a new project, open to the whole team. */
export function DeclareProjectDialog({
  open,
  onOpenChange,
  onConfirm,
  titre = "Déclarer un projet",
}: DeclareProjectDialogProps) {
  const [label, setLabel] = useState("");
  const [enCours, setEnCours] = useState(false);

  const valide = label.trim().length > 0;

  async function confirmer() {
    if (!valide) return;
    setEnCours(true);
    try {
      await onConfirm(label.trim());
      setLabel("");
      onOpenChange(false);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{titre}</DialogTitle>
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
              if (event.key === "Enter") confirmer();
            }}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={confirmer} disabled={!valide || enCours}>
            Déclarer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
