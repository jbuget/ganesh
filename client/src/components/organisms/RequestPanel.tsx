"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { RequestStateMark } from "@/components/atoms/RequestStateMark";
import { SheetRow } from "@/components/atoms/SheetRow";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import { SidePanel } from "@/components/atoms/SidePanel";
import { RequestSheet } from "@/components/molecules/RequestSheet";
import { Button } from "@/components/ui/button";
import type { FillInRequestRequest, RequestResponse } from "@/lib/api/generated/model";
import { formatParisDateTime } from "@/lib/instants";
import { missingBeforeSubmitting, sayMissing } from "@/lib/requests";

interface RequestPanelProps {
  request: RequestResponse;
  /** False for whoever is only reading somebody else's need. */
  mine: boolean;
  onChange: (change: Partial<FillInRequestRequest>) => void | Promise<void>;
  onSubmit: () => void | Promise<void>;
  onWithdraw: () => void | Promise<void>;
  onDelete: () => void | Promise<void>;
  onClose: () => void;
  /** What the team may do with it, when the reader is on the team. */
  footer?: React.ReactNode;
  /**
   * What closes the sheet, when the reader is allowed to see it.
   *
   * The journal is the team's reading: what a requester has to know of their
   * own need — where it stands, and why — the sheet above already tells them.
   */
  journal?: React.ReactNode;
}

/**
 * One need, opened beside the list.
 *
 * A draft is written here and handed over from here: the two gestures belong
 * together, and a « Soumettre » sitting on the list would be a click made
 * without having read what is being sent.
 *
 * Once handed over the sheet stops moving, and says so: the decision bears on
 * a text that has stopped changing. Taking it back is what reopens it.
 */
export function RequestPanel({
  request,
  mine,
  onChange,
  onSubmit,
  onWithdraw,
  onDelete,
  onClose,
  footer,
  journal,
}: RequestPanelProps) {
  const [busy, setBusy] = useState(false);
  const editable = mine && request.state === "draft";
  const missing = missingBeforeSubmitting(request);

  async function run(gesture: () => void | Promise<void>) {
    setBusy(true);
    try {
      await gesture();
    } finally {
      setBusy(false);
    }
  }

  return (
    <SidePanel label={request.title} onClose={onClose}>
      <header className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <h2 className="min-w-0 flex-1 truncate text-lg font-semibold text-slate-900">
          {request.title}
        </h2>
        <button
          type="button"
          aria-label="Fermer"
          onClick={onClose}
          className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="size-4" aria-hidden />
        </button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 py-4">
        <SheetSectionTitle>État</SheetSectionTitle>

        <SheetRow title="Statut">
          <RequestStateMark value={request.state} />
        </SheetRow>

        <SheetRow title="Demandeur">
          <span className="text-sm text-slate-700">{request.requester.label}</span>
        </SheetRow>

        <SheetRow title="Déposée le">
          <span className="text-sm text-slate-700">
            {formatParisDateTime(request.created_at)}
          </span>
        </SheetRow>

        {request.decided_at && (
          <SheetRow title="Arbitrée">
            <span className="text-sm text-slate-700">
              {formatParisDateTime(request.decided_at)}
              {request.decided_by && ` · ${request.decided_by.label}`}
            </span>
          </SheetRow>
        )}

        {request.decision_note && (
          <SheetRow title="Motif">
            <p className="whitespace-pre-wrap text-sm text-slate-700">
              {request.decision_note}
            </p>
          </SheetRow>
        )}

        <RequestSheet request={request} editable={editable} onChange={onChange} />

        {journal}
      </div>

      {mine && (
        <footer className="shrink-0 space-y-2 border-t border-slate-200 px-5 py-4">
          {request.state === "draft" && (
            <>
              {missing.length > 0 && (
                <p className="text-xs text-slate-500">
                  Il manque {sayMissing(missing)} avant de pouvoir soumettre.
                </p>
              )}
              <div className="flex items-center gap-2">
                <Button
                  className="cursor-pointer"
                  disabled={busy || missing.length > 0}
                  onClick={() => void run(onSubmit)}
                >
                  Soumettre
                </Button>
                <Button
                  variant="outline"
                  className="cursor-pointer"
                  disabled={busy}
                  onClick={() => void run(onDelete)}
                >
                  Supprimer
                </Button>
              </div>
            </>
          )}

          {request.state === "submitted" && (
            <div className="space-y-2">
              {/* The button says the intention and the price of it in one
                  breath. « Modifier » alone would let somebody fix a typo and
                  put their need to sleep without knowing: taking it back is
                  what takes it out of the queue, and nobody waits for it
                  until it is handed over again. */}
              <p className="text-xs text-slate-500">
                Soumise : la fiche ne bouge plus. La reprendre la retire de la file
                d&apos;arbitrage, et il faudra la soumettre à nouveau.
              </p>
              <Button
                variant="outline"
                className="cursor-pointer"
                disabled={busy}
                onClick={() => void run(onWithdraw)}
              >
                Reprendre pour modifier
              </Button>
            </div>
          )}
        </footer>
      )}

      {footer}
    </SidePanel>
  );
}
