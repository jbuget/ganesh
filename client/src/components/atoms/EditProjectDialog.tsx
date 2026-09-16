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
import type { ProjectResponse } from "@/lib/api/generated/model";

export interface ProjectEdits {
  label: string;
  estime_j: number | null;
  monday_item_id: string | null;
}

interface EditProjectDialogProps {
  project: ProjectResponse | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: (edits: ProjectEdits) => Promise<void>;
}

/**
 * Edition d'une mission : libelle, estime, rattachement Monday.
 *
 * Le parent remonte ce composant via une `key` a chaque mission ouverte : c'est
 * ainsi que React recommande de repartir d'un etat neuf, plutot que de le
 * reinitialiser depuis un effet.
 */
export function EditProjectDialog({
  project,
  onOpenChange,
  onConfirm,
}: EditProjectDialogProps) {
  const [label, setLabel] = useState(project?.label ?? "");
  const [estime, setEstime] = useState(
    project?.estime_j != null ? String(project.estime_j) : "",
  );
  const [mondayId, setMondayId] = useState(project?.monday_item_id ?? "");
  const [enCours, setEnCours] = useState(false);

  const valide = label.trim().length > 0;

  async function confirmer() {
    if (!valide) return;
    setEnCours(true);
    try {
      await onConfirm({
        label: label.trim(),
        estime_j: estime.trim() === "" ? null : Number(estime),
        monday_item_id: mondayId.trim() || null,
      });
      onOpenChange(false);
    } finally {
      setEnCours(false);
    }
  }

  const estLot = project?.kind === "lot";

  return (
    <Dialog open={project !== null} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Modifier {estLot ? "le sous-projet" : "le projet"}</DialogTitle>
          <DialogDescription>
            Chaque modification est tracée et visible de toute l&apos;équipe.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="edit-label">Nom</Label>
            <Input
              id="edit-label"
              value={label}
              autoFocus
              onChange={(event) => setLabel(event.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="edit-estime">Estimé (jours)</Label>
            <Input
              id="edit-estime"
              type="number"
              min={0}
              step={0.5}
              value={estime}
              placeholder="Non estimé"
              onChange={(event) => setEstime(event.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="edit-monday">Identifiant Monday</Label>
            <Input
              id="edit-monday"
              value={mondayId}
              placeholder="5091544837"
              onChange={(event) => setMondayId(event.target.value)}
            />
            <p className="text-xs text-slate-500">
              Sans identifiant, la mission ne remontera pas dans Monday.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={confirmer} disabled={!valide || enCours}>
            Enregistrer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
