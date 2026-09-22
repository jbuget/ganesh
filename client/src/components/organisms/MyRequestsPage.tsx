"use client";

import { useState } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { RequestStateMark } from "@/components/atoms/RequestStateMark";
import { NewRequestDialog } from "@/components/molecules/NewRequestDialog";
import { PageLayout } from "@/components/organisms/PageLayout";
import { RequestPanel } from "@/components/organisms/RequestPanel";
import { Button } from "@/components/ui/button";
import { departmentLabel } from "@/lib/departments";
import { useOpenedRequest } from "@/lib/opened-request";
import { formatParisDateTime } from "@/lib/instants";
import { STRONG_RULE } from "@/lib/table-frame";
import { useMyRequestsScreen } from "@/lib/use-my-requests";

/**
 * The needs one has expressed oneself, and the one screen a requester reaches.
 *
 * Deliberately the whole of their Ganesh: whoever comes to ask for something
 * has no business in the team's month, its board or its plan. What they get
 * instead is the one thing they came for, and the state of what they asked
 * before.
 *
 * Rows rather than a table: three columns of metadata would say less than the
 * title, the state and the date, and a list somebody reads four times a year
 * has nothing to gain from a frame.
 */
export function MyRequestsPage() {
  const screen = useMyRequestsScreen();
  // Held by the URL, as on the team's list: a need opened is a need one can
  // send to somebody, and going back closes it.
  const panel = useOpenedRequest();
  const [filing, setFiling] = useState(false);
  const opened = panel.openedRequest ? screen.find(panel.openedRequest) : null;

  const header = (
    <PageHeader
      title="Mes demandes"
      subtitle="Ce que vous avez demandé, et où cela en est."
      actions={
        <Button className="cursor-pointer" onClick={() => setFiling(true)}>
          Nouvelle demande
        </Button>
      }
    />
  );

  return (
    <PageLayout header={header}>
      {screen.isLoading ? (
        <p className="text-sm text-slate-500">Chargement…</p>
      ) : screen.requests.length === 0 ? (
        <p className="text-sm text-slate-500">
          Aucune demande pour le moment. Décrivez un besoin : il sera lu par
          l&apos;équipe et porté au COMEX par le sponsor que vous désignez.
        </p>
      ) : (
        <ul className={`divide-y divide-slate-200 rounded-none border ${STRONG_RULE}`}>
          {screen.requests.map((request) => (
            <li key={request.id}>
              <button
                type="button"
                onClick={() => panel.open(request.id)}
                className="flex w-full cursor-pointer items-center gap-4 bg-white px-4 py-3 text-left transition-colors hover:bg-slate-50"
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium text-slate-900">
                    {request.title}
                  </span>
                  <span className="block truncate text-xs text-slate-500">
                    {request.departments.map(departmentLabel).join(", ")}
                    {" · "}
                    {formatParisDateTime(request.created_at)}
                  </span>
                </span>
                <span className="shrink-0 text-sm">
                  <RequestStateMark value={request.state} />
                </span>
              </button>
            </li>
          ))}
        </ul>
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
          mine
          onChange={(change) => screen.fillIn(opened, change)}
          onSubmit={() => screen.submit(opened.id)}
          onWithdraw={() => screen.withdraw(opened.id)}
          onDelete={async () => {
            await screen.remove(opened.id);
            panel.close();
          }}
          onClose={panel.close}
        />
      )}
    </PageLayout>
  );
}
