"use client";

import { useState } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { ApiKeyRow } from "@/components/molecules/ApiKeyRow";
import { CreateApiKeyDialog } from "@/components/molecules/CreateApiKeyDialog";
import { MintedApiKeyPanel } from "@/components/molecules/MintedApiKeyPanel";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useTeammates } from "@/lib/api/queries";
import { useApiKeysScreen } from "@/lib/use-api-keys";

/**
 * The service accounts.
 *
 * Anyone may look at the table: it carries no secret — the public half of a
 * key helps nobody use it — and a key nobody looks at is a key nobody notices
 * has been idle for months. Only minting and cutting are a manager's.
 */
export function ApiKeysPage() {
  const screen = useApiKeysScreen();
  const { teammates } = useTeammates();
  const [creating, setCreating] = useState(false);

  return (
    <PageLayout
      header={
        <PageHeader
          title="API"
          subtitle={
            screen.isManager
              ? "Les comptes de service qui accèdent à l'API. Chaque création et chaque révocation est tracée."
              : "Consultable par toute l'équipe. Seul un manager crée ou révoque une clé."
          }
          actions={
            screen.isManager ? (
              <Button className="cursor-pointer" onClick={() => setCreating(true)}>
                Créer une clé
              </Button>
            ) : undefined
          }
        />
      }
    >
      <div className="max-w-[1100px]">
        {screen.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}

        {!screen.isLoading && screen.keys.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">
            {screen.isManager
              ? "Aucune clé. Créez-en une pour qu'un service externe puisse lire l'API sans compte utilisateur."
              : "Aucune clé."}
          </p>
        )}

        {screen.keys.length > 0 && (
          // The same setting as the other tables: the shadcn container opens a
          // scrolling context that would hold the header inside the table.
          <div className="[&_[data-slot=table-container]]:overflow-visible">
            <Table>
              <TableHeader className="sticky top-0 z-10 [&_th]:border-b [&_th]:border-slate-200 [&_th]:bg-slate-50">
                <TableRow>
                  <TableHead>Clé</TableHead>
                  <TableHead>Périmètres</TableHead>
                  <TableHead>Responsable</TableHead>
                  <TableHead>Dernier appel</TableHead>
                  <TableHead>Expiration</TableHead>
                  <TableHead>État</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {screen.keys.map((apiKey) => (
                  <ApiKeyRow
                    key={apiKey.id}
                    apiKey={apiKey}
                    canRevoke={screen.isManager}
                    onRevoke={screen.revoke}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <CreateApiKeyDialog
        open={creating}
        onOpenChange={setCreating}
        teammates={teammates}
        onCreate={screen.create}
      />

      <MintedApiKeyPanel minted={screen.minted} onClose={screen.dismissMinted} />
    </PageLayout>
  );
}
