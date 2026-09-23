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
import type { ProjectKind } from "@/lib/api/generated/model";

/**
 * What each kind is called on the screen that declares it.
 *
 * The two ask for exactly the same thing — a name — and are not announced the
 * same way: a project joins the reference list, a package joins a project.
 * Keeping the wording here rather than in props keeps the four sentences of
 * one kind together, where they can be read as one.
 */
const WORDING = {
  project: {
    title: "Déclarer un projet",
    announcement:
      "Le projet sera ajouté au référentiel commun et visible de toute l'équipe.",
    field: "Nom du projet",
    placeholder: "Refonte extranet copropriété",
  },
  work_package: {
    title: "Déclarer un sous-projet",
    announcement:
      "Le sous-projet sera rattaché au projet et visible de toute l'équipe.",
    field: "Nom du sous-projet",
    placeholder: "Reprise de données",
  },
} as const;

interface DeclareProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (label: string) => Promise<void>;
  /**
   * What is being declared; a project unless said otherwise.
   *
   * Off-project work is not declared here: absences and training are set up
   * once, and are not what one adds on the way past a board.
   */
  kind?: Extract<ProjectKind, "project" | "work_package">;
}

/** Declaring a new mission, open to the whole team. */
export function DeclareProjectDialog({
  open,
  onOpenChange,
  onConfirm,
  kind = "project",
}: DeclareProjectDialogProps) {
  const words = WORDING[kind];
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
          <DialogTitle>{words.title}</DialogTitle>
          <DialogDescription>{words.announcement}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="project-label">{words.field}</Label>
          <Input
            id="project-label"
            value={label}
            autoFocus
            placeholder={words.placeholder}
            onChange={(event) => setLabel(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void confirm();
            }}
          />
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
            onClick={confirm}
            disabled={!isValid || busy}
          >
            Déclarer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
