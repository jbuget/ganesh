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
import type { ProjectKind, WorkNature } from "@/lib/api/generated/model";
import { WORK_NATURES } from "@/lib/work-natures";

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
  onConfirm: (label: string, nature: WorkNature | null) => Promise<void>;
  /**
   * Whether to ask which trade the time will be declared under.
   *
   * Asked only where the mission is declared in order to be worked on right
   * away — from one's own month. A mission carries no time until it is cut
   * into trades, so declaring one from there without saying which would land
   * the reader on a row they cannot write in.
   */
  asksForTrade?: boolean;
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
  asksForTrade = false,
}: DeclareProjectDialogProps) {
  const words = WORDING[kind];
  const [label, setLabel] = useState("");
  const [nature, setNature] = useState<WorkNature>("development");
  const [busy, setBusy] = useState(false);

  const isValid = label.trim().length > 0;

  async function confirm() {
    if (!isValid) return;
    setBusy(true);
    try {
      await onConfirm(label.trim(), asksForTrade ? nature : null);
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

        {asksForTrade && (
          <div className="grid gap-2">
            <Label htmlFor="project-trade">Votre activité sur ce projet</Label>
            <div className="flex flex-wrap gap-1.5" id="project-trade">
              {WORK_NATURES.map((trade) => (
                <button
                  key={trade.value}
                  type="button"
                  aria-pressed={nature === trade.value}
                  onClick={() => setNature(trade.value)}
                  className={[
                    "cursor-pointer rounded-md border px-2 py-1 text-xs transition-colors",
                    nature === trade.value
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-300 text-slate-700 hover:border-slate-400 hover:bg-slate-50",
                  ].join(" ")}
                >
                  {trade.label}
                </button>
              ))}
            </div>
          </div>
        )}

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
