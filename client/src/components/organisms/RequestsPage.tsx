"use client";

import { useState } from "react";

import { ConvertRequestDialog } from "@/components/atoms/ConvertRequestDialog";
import { DecideRequestDialog } from "@/components/atoms/DecideRequestDialog";
import { PageHeader } from "@/components/atoms/PageHeader";
import { NewRequestDialog } from "@/components/molecules/NewRequestDialog";
import { RequestFilters } from "@/components/molecules/RequestFilters";
import { PageLayout } from "@/components/organisms/PageLayout";
import { RequestPanel } from "@/components/organisms/RequestPanel";
import { RequestsTable } from "@/components/organisms/RequestsTable";
import { Button } from "@/components/ui/button";
import type { RequestState } from "@/lib/api/generated/model";
import { useOpenedRequest } from "@/lib/opened-request";
import { mayArbitrate } from "@/lib/requests";
import { useRequestFilters } from "@/lib/use-request-filters";
import { useRequestsScreen } from "@/lib/use-requests";

/**
 * What the company has asked for, and what the team decided of it.
 *
 * It opens on what is waiting to be weighed: one comes here to answer, and a
 * list opening on everything ever asked for would bury the three that need an
 * answer today. « Effacer » takes that default off with the rest.
 *
 * A table rather than a board: the states are a cycle of arbitration and not
 * a flow one drags things through, and the board already steers what runs.
 *
 * Anyone on the team may file a need of their own from here — most of the
 * team sits in the COMOP too — and reads it in the same list, drafts
 * included, since one's own draft is nobody else's to be hidden from.
 */
export function RequestsPage() {
  const { filters, hasFilter, set, clear } = useRequestFilters();
  const screen = useRequestsScreen(filters);
  const panel = useOpenedRequest();
  const [filing, setFiling] = useState(false);
  const [deciding, setDeciding] = useState<RequestState | null>(null);
  const [converting, setConverting] = useState(false);

  const opened = panel.openedRequest ? screen.find(panel.openedRequest) : null;
  const mine = opened?.requester.id === screen.user?.id;

  return (
    <PageLayout
      header={
        <>
          <PageHeader
            title="Demandes"
            subtitle="Ce que l'entreprise demande, et ce qu'on en a décidé."
            actions={
              <Button className="cursor-pointer" onClick={() => setFiling(true)}>
                Nouvelle demande
              </Button>
            }
          />

          {/* With the header, outside the scrolling area: the question asked
              of the list must stay readable and editable, whether one has
              gone thirty rows down or not. */}
          <RequestFilters
            filters={filters}
            hasFilter={hasFilter}
            onChange={set}
            onClear={clear}
            visible={screen.visible}
            total={screen.total}
          />
        </>
      }
    >
      {screen.isLoading ? (
        <p className="text-sm text-slate-500">Chargement…</p>
      ) : screen.requests.length === 0 ? (
        <p className="text-sm text-slate-500">
          {screen.total === 0
            ? "Aucune demande pour le moment."
            : "Aucune demande ne correspond à ces critères."}
        </p>
      ) : (
        <RequestsTable requests={screen.requests} onOpen={panel.open} />
      )}

      <NewRequestDialog
        open={filing}
        onOpenChange={setFiling}
        onConfirm={async (draft) => {
          const filed = await screen.file(draft);
          panel.open(filed.id);
        }}
      />

      {opened && (
        <RequestPanel
          request={opened}
          mine={mine}
          onChange={(change) => screen.fillIn(opened, change)}
          onSubmit={() => screen.submit(opened.id)}
          onWithdraw={() => screen.withdraw(opened.id)}
          onDelete={async () => {
            await screen.remove(opened.id);
            panel.close();
          }}
          onClose={panel.close}
          footer={
            mayArbitrate(opened, screen.user) ? (
              <footer className="shrink-0 space-y-2 border-t border-slate-200 px-5 py-4">
                <p className="text-xs text-slate-500">
                  {opened.state === "submitted"
                    ? "À arbitrer."
                    : opened.state === "accepted"
                      ? "Acceptée : il reste à en faire un projet."
                      : "Déjà arbitrée : la décision peut être rejouée tant que rien n'a été construit."}
                </p>
                <div className="flex items-center gap-2">
                  {opened.state === "accepted" ? (
                    <Button
                      className="cursor-pointer"
                      onClick={() => setConverting(true)}
                    >
                      Convertir en projet
                    </Button>
                  ) : (
                    <Button
                      className="cursor-pointer"
                      onClick={() => setDeciding("accepted")}
                    >
                      Accepter
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => setDeciding("deferred")}
                  >
                    Plus tard
                  </Button>
                  <Button
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => setDeciding("rejected")}
                  >
                    Refuser
                  </Button>
                </div>
              </footer>
            ) : null
          }
        />
      )}

      {converting && opened && (
        <ConvertRequestDialog
          open
          onOpenChange={setConverting}
          onConfirm={async (kind, parentId) => {
            await screen.convert(opened.id, kind, parentId);
            setConverting(false);
          }}
        />
      )}

      <DecideRequestDialog
        decision={deciding}
        onOpenChange={(open) => {
          if (!open) setDeciding(null);
        }}
        onConfirm={async (note) => {
          if (!opened || !deciding) return;
          await screen.decide(opened.id, deciding, note);
          setDeciding(null);
        }}
      />
    </PageLayout>
  );
}
