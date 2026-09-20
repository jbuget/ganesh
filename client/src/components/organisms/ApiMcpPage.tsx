"use client";

import { useState } from "react";

import { PageHeader } from "@/components/atoms/PageHeader";
import { CreateApiKeyDialog } from "@/components/molecules/CreateApiKeyDialog";
import { MintedApiKeyPanel } from "@/components/molecules/MintedApiKeyPanel";
import { ApiKeyPanel } from "@/components/organisms/ApiKeyPanel";
import { ApiKeysTable } from "@/components/organisms/ApiKeysTable";
import { McpTab } from "@/components/organisms/McpTab";
import { PageLayout } from "@/components/organisms/PageLayout";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTeammates } from "@/lib/api/queries";
import { useApiKeysScreen } from "@/lib/use-api-keys";

/**
 * The service accounts, and the terminal clients they let in.
 *
 * Anyone may look at the table: it carries no secret — the public half of a
 * key helps nobody use it — and a key nobody looks at is a key nobody notices
 * has been idle for months. Only minting and cutting are a manager's.
 *
 * Two tabs, and the order between them is the reading: « API » is what a key
 * *is*, « MCP » is what one does with it. One cannot follow the second
 * without having been handed a key by the first, so the key comes first.
 *
 * « Créer une clé » belongs to the first tab alone. The button acts on the
 * table under it, and left standing over a page of configuration snippets it
 * would read as the gesture that branches a terminal.
 */
export function ApiMcpPage() {
  const screen = useApiKeysScreen();
  const { teammates } = useTeammates();
  const [creating, setCreating] = useState(false);
  const [tab, setTab] = useState("api");

  return (
    <PageLayout
      header={
        <PageHeader
          title="API / MCP"
          subtitle={
            screen.isManager
              ? "Quelles machines accèdent à Ganesh, ce que chaque clé ouvre, et comment y brancher un terminal. Chaque création et chaque révocation est tracée."
              : "Quelles machines accèdent à Ganesh, ce que chaque clé ouvre, et comment y brancher un terminal. Seul un manager crée ou révoque une clé."
          }
          actions={
            screen.isManager && tab === "api" ? (
              <Button className="cursor-pointer" onClick={() => setCreating(true)}>
                Créer une clé
              </Button>
            ) : undefined
          }
        />
      }
    >
      <Tabs
        value={tab}
        onValueChange={(value) => setTab(String(value))}
        className="flex flex-col gap-4"
      >
        <TabsList className="w-fit">
          <TabsTrigger value="api" className="cursor-pointer">
            API
          </TabsTrigger>
          <TabsTrigger value="mcp" className="cursor-pointer">
            MCP
          </TabsTrigger>
        </TabsList>

        <TabsContent value="api">
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
              <ApiKeysTable keys={screen.keys} onOpen={screen.open} />
            )}
          </div>
        </TabsContent>

        <TabsContent value="mcp">
          <McpTab />
        </TabsContent>
      </Tabs>

      <CreateApiKeyDialog
        open={creating}
        onOpenChange={setCreating}
        teammates={teammates}
        onCreate={screen.create}
      />

      {screen.opened && (
        <ApiKeyPanel
          apiKey={screen.opened}
          editable={screen.isManager}
          onRename={screen.rename}
          onChangeScopes={screen.changeScopes}
          onRevoke={screen.revoke}
          onClose={screen.close}
        />
      )}

      <MintedApiKeyPanel minted={screen.minted} onClose={screen.dismissMinted} />
    </PageLayout>
  );
}
