"use client";

import { RotateCcw, Save } from "lucide-react";
import { useState } from "react";

import { SaveSimulationDialog } from "@/components/atoms/SaveSimulationDialog";
import { SimulationPicker } from "@/components/atoms/SimulationPicker";
import { Button } from "@/components/ui/button";
import type { SimulationResponse } from "@/lib/api/generated/model";

interface SimulationBarProps {
  simulations: SimulationResponse[];
  opened: SimulationResponse | null;
  /** Whether anything is supposed at all, saved or not. */
  isHypothesis: boolean;
  /** Whether what is on screen has drifted from what was saved. */
  hasUnsavedChanges: boolean;
  saveError: string | null;
  /**
   * Whether a scenario may be kept at all.
   *
   * Arbitrating is local — one reorders the backlog and puts people on
   * missions to see what it would cost, and nothing of that touches the
   * server. Keeping the question is the write, and it is the only thing a
   * guest is short of here.
   */
  mayKeep: boolean;
  onOpen: (simulation: SimulationResponse | null) => void;
  onSaveAs: (name: string) => Promise<boolean>;
  onSaveOver: () => Promise<void>;
  onDelete: (simulationId: number) => void;
  onReset: () => void;
}

/**
 * Where a scenario is chosen, kept, or thrown away.
 *
 * Two ways of saving, deliberately told apart: rewriting the scenario one has
 * open, and starting a new one. Folding them into a single button would mean
 * guessing which the reader meant, and guessing wrong silently overwrites
 * somebody else's thinking.
 */
export function SimulationBar({
  simulations,
  opened,
  isHypothesis,
  hasUnsavedChanges,
  saveError,
  mayKeep,
  onOpen,
  onSaveAs,
  onSaveOver,
  onDelete,
  onReset,
}: SimulationBarProps) {
  const [isNaming, setNaming] = useState(false);

  return (
    <div className="flex items-center gap-2">
      <SimulationPicker
        simulations={simulations}
        opened={opened}
        onOpen={onOpen}
        onDelete={mayKeep ? onDelete : undefined}
      />

      {mayKeep && opened && hasUnsavedChanges && (
        <Button
          variant="outline"
          size="sm"
          className="cursor-pointer"
          onClick={() => void onSaveOver()}
        >
          <Save className="size-4" aria-hidden />
          Enregistrer
        </Button>
      )}

      {mayKeep && isHypothesis && (
        <Button
          variant="outline"
          size="sm"
          className="cursor-pointer"
          onClick={() => setNaming(true)}
        >
          {opened ? "Enregistrer sous…" : "Enregistrer la simulation"}
        </Button>
      )}

      {isHypothesis && (
        <Button
          variant="ghost"
          size="sm"
          className="cursor-pointer"
          onClick={onReset}
          title="Revenir à l'ordre de l'équipe"
        >
          <RotateCcw className="size-4" aria-hidden />
          Réinitialiser
        </Button>
      )}

      <SaveSimulationDialog
        open={isNaming}
        onOpenChange={setNaming}
        onConfirm={onSaveAs}
        error={saveError}
      />
    </div>
  );
}
