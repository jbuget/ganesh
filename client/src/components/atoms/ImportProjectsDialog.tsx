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
import type { ImportReportResponse } from "@/lib/api/generated/model";
import { COLONNES, parseProjectsCsv } from "@/lib/csv-import";

interface ImportProjectsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (contenu: string) => Promise<ImportReportResponse>;
}

/** Import d'un referentiel depuis un export tableur. Reserve aux managers. */
export function ImportProjectsDialog({
  open,
  onOpenChange,
  onImport,
}: ImportProjectsDialogProps) {
  const [contenu, setContenu] = useState("");
  const [rapport, setRapport] = useState<ImportReportResponse | null>(null);
  const [enCours, setEnCours] = useState(false);

  const lignes = parseProjectsCsv(contenu);

  async function importer() {
    setEnCours(true);
    try {
      setRapport(await onImport(contenu));
    } finally {
      setEnCours(false);
    }
  }

  function fermer(ouvert: boolean) {
    if (!ouvert) {
      setContenu("");
      setRapport(null);
    }
    onOpenChange(ouvert);
  }

  return (
    <Dialog open={open} onOpenChange={fermer}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Importer un référentiel</DialogTitle>
          <DialogDescription>
            Collez un export tableur. Les missions déjà connues sont ignorées,
            l&apos;import peut donc être rejoué sans risque.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="csv">Colonnes reconnues : {COLONNES.join(", ")}</Label>
          <textarea
            id="csv"
            rows={8}
            value={contenu}
            placeholder={"label;kind;parent_label;estime_j\nPortail;projet;;20"}
            onChange={(event) => {
              setContenu(event.target.value);
              setRapport(null);
            }}
            className="w-full rounded-md border border-slate-300 p-2 font-mono text-xs"
          />
          <p className="text-xs text-slate-500">
            {lignes.length} ligne(s) détectée(s).
          </p>
        </div>

        {rapport && (
          <div className="space-y-2 rounded-md border border-slate-300 bg-slate-50 p-3 text-sm">
            <p>
              <strong>{rapport.crees}</strong> mission(s) créée(s),{" "}
              <strong>{rapport.ignores}</strong> déjà connue(s).
            </p>
            {rapport.erreurs.length > 0 && (
              <ul className="list-inside list-disc text-red-800">
                {rapport.erreurs.map((erreur) => (
                  <li key={erreur}>{erreur}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => fermer(false)}>
            Fermer
          </Button>
          <Button onClick={importer} disabled={lignes.length === 0 || enCours}>
            Importer {lignes.length > 0 && `(${lignes.length})`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
