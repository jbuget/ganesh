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
import { COLUMNS, parseProjectsCsv } from "@/lib/csv-import";

interface ImportProjectsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (content: string) => Promise<ImportReportResponse>;
}

/** Importing a reference list from a spreadsheet export. Managers only. */
export function ImportProjectsDialog({
  open,
  onOpenChange,
  onImport,
}: ImportProjectsDialogProps) {
  const [content, setContent] = useState("");
  const [report, setReport] = useState<ImportReportResponse | null>(null);
  const [busy, setBusy] = useState(false);

  const lines = parseProjectsCsv(content);

  async function runImport() {
    setBusy(true);
    try {
      setReport(await onImport(content));
    } finally {
      setBusy(false);
    }
  }

  function close(isOpen: boolean) {
    if (!isOpen) {
      setContent("");
      setReport(null);
    }
    onOpenChange(isOpen);
  }

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Importer un référentiel</DialogTitle>
          <DialogDescription>
            Collez un export tableur. Les missions déjà connues sont ignorées,
            l&apos;import peut donc être rejoué sans risque.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-2">
          <Label htmlFor="csv">
            Colonnes reconnues : {Object.keys(COLUMNS).join(", ")}
          </Label>
          <textarea
            id="csv"
            rows={8}
            value={content}
            placeholder={"label;kind;parent_label;estime_j\nPortail;projet;;20"}
            onChange={(event) => {
              setContent(event.target.value);
              setReport(null);
            }}
            className="w-full rounded-md border border-slate-300 p-2 font-mono text-xs"
          />
          <p className="text-xs text-slate-500">{lines.length} ligne(s) détectée(s).</p>
        </div>

        {report && (
          <div className="space-y-2 rounded-md border border-slate-300 bg-slate-50 p-3 text-sm">
            <p>
              <strong>{report.created}</strong> mission(s) créée(s),{" "}
              <strong>{report.skipped}</strong> déjà connue(s).
            </p>
            {report.errors.length > 0 && (
              <ul className="list-inside list-disc text-red-800">
                {report.errors.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => close(false)}>
            Fermer
          </Button>
          <Button onClick={runImport} disabled={lines.length === 0 || busy}>
            Importer {lines.length > 0 && `(${lines.length})`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
