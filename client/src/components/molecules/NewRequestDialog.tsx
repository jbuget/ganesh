"use client";

import { useState } from "react";

import { DepartmentPicker } from "@/components/atoms/DepartmentPicker";
import { SponsorsPicker } from "@/components/atoms/SponsorsPicker";
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
import type { Department } from "@/lib/api/generated/model";

interface NewRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (draft: {
    title: string;
    departments: Department[];
    sponsor_ids: number[];
  }) => Promise<void>;
}

/**
 * Opening a need: the three things nobody else can supply.
 *
 * What it is called, whom it concerns, and who carries it to the COMEX. The
 * rest is written afterwards, in the panel that opens on it — a form asking
 * for eight things at once is a form nobody finishes.
 */
export function NewRequestDialog({
  open,
  onOpenChange,
  onConfirm,
}: NewRequestDialogProps) {
  const [title, setTitle] = useState("");
  const [departments, setDepartments] = useState<Department[]>([]);
  const [sponsorIds, setSponsorIds] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);

  const isValid =
    title.trim().length > 0 && departments.length > 0 && sponsorIds.length > 0;

  function forget() {
    setTitle("");
    setDepartments([]);
    setSponsorIds([]);
  }

  async function confirm() {
    if (!isValid) return;
    setBusy(true);
    try {
      await onConfirm({
        title: title.trim(),
        departments,
        sponsor_ids: sponsorIds,
      });
      forget();
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) forget();
        onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nouvelle demande</DialogTitle>
          <DialogDescription>
            Décrivez le besoin dans la fiche qui s&apos;ouvrira ensuite. Rien n&apos;est
            transmis tant que vous ne l&apos;avez pas soumise.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="request-title">Intitulé</Label>
          <Input
            id="request-title"
            value={title}
            autoFocus
            placeholder="Relances de paiement faites à la main"
            onChange={(event) => setTitle(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void confirm();
            }}
          />
        </div>

        <div className="grid gap-2">
          <Label>Départements concernés</Label>
          <DepartmentPicker values={departments} onChange={setDepartments} />
        </div>

        <div className="grid gap-2">
          <Label>Sponsors au COMEX</Label>
          <SponsorsPicker values={sponsorIds} onChange={setSponsorIds} />
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
            Créer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
