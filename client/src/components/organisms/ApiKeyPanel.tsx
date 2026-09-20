"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { ApiKeyStateBadge } from "@/components/atoms/ApiKeyStateBadge";
import { EditableTitle } from "@/components/atoms/EditableTitle";
import { RevokeApiKeyDialog } from "@/components/atoms/RevokeApiKeyDialog";
import { SidePanel } from "@/components/atoms/SidePanel";
import { ScopePicker } from "@/components/molecules/ScopePicker";
import { Button } from "@/components/ui/button";
import type { ApiKeyResponse, ApiKeyScope } from "@/lib/api/generated/model";
import { isUsable, pruneCovered, scopeLabel } from "@/lib/api-keys";
import { formatSpelledDate } from "@/lib/dates";
import { parisDay } from "@/lib/instants";

interface ApiKeyPanelProps {
  apiKey: ApiKeyResponse;
  /** Minting and correcting a key are a manager's, as revoking is. */
  editable: boolean;
  onRename: (keyId: number, name: string) => void | Promise<void>;
  onChangeScopes: (keyId: number, scopes: ApiKeyScope[]) => void | Promise<void>;
  onRevoke: (keyId: number) => void | Promise<void>;
  onClose: () => void;
}

/**
 * One row of the sheet: its heading on the left, its value on the right.
 *
 * The same grammar as the mission sheet and the teammate panel — a constant
 * heading width gives the top-to-bottom scan something to lean on.
 */
function Row({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="w-36 shrink-0 pt-0.5 text-sm text-slate-500">{title}</span>
      <div className="min-w-0 flex-1 text-sm">{children}</div>
    </div>
  );
}

/** A date, or a dash where there is nothing to say. */
function Day({ iso }: { iso: string | null }) {
  if (iso === null) return <span className="text-slate-400">—</span>;
  return <span className="text-slate-700">{formatSpelledDate(parisDay(iso))}</span>;
}

/**
 * A service account, opened beside the list.
 *
 * Two things are corrected here and nothing else: the name the team reads it
 * by, and what it opens. The secret is not reissued, the owner is not swapped
 * and the expiry is not moved — those are reasons to mint a new key, not to
 * bend an old one. A revoked key is frozen: it says what a machine was called
 * while it worked, and the audit refers to that.
 */
export function ApiKeyPanel({
  apiKey,
  editable,
  onRename,
  onChangeScopes,
  onRevoke,
  onClose,
}: ApiKeyPanelProps) {
  const [confirming, setConfirming] = useState(false);
  // A cut key is a piece of the audit: read, never rewritten.
  const open = isUsable(apiKey) || apiKey.state === "expired";
  const changeable = editable && open;

  return (
    <SidePanel label={apiKey.name} onClose={onClose}>
      <header className="border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <EditableTitle
            label={apiKey.name}
            hint="Renommer la clé"
            onRename={changeable ? (name) => onRename(apiKey.id, name) : undefined}
          />

          <button
            type="button"
            aria-label="Fermer"
            onClick={onClose}
            className="cursor-pointer rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="size-4" aria-hidden />
          </button>
        </div>

        {/* Under the name, the only half of the key that is ever shown again. */}
        <code className="mt-1 block font-mono text-xs text-slate-500">
          {apiKey.masked}
        </code>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto px-5 py-4">
        <section className="space-y-2">
          <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
            Identité
          </h3>

          <div className="divide-y divide-slate-100">
            <Row title="État">
              <ApiKeyStateBadge state={apiKey.state} />
            </Row>
            <Row title="Compte associé">
              <span className="text-slate-700">{apiKey.owner.display_name}</span>
            </Row>
            <Row title="Créée par">
              <span className="text-slate-700">{apiKey.created_by.display_name}</span>
            </Row>
            <Row title="Créée le">
              <Day iso={apiKey.created_at} />
            </Row>
            <Row title="Dernière utilisation">
              <Day iso={apiKey.last_used_at} />
            </Row>
            <Row title="Expiration">
              <Day iso={apiKey.expires_at} />
            </Row>
            {apiKey.revoked_at && (
              <Row title="Révoquée le">
                <span className="flex flex-wrap items-center gap-x-2 text-slate-700">
                  {formatSpelledDate(parisDay(apiKey.revoked_at))}
                  {apiKey.revoked_by && (
                    <span className="text-xs text-slate-500">
                      par {apiKey.revoked_by.display_name}
                    </span>
                  )}
                </span>
              </Row>
            )}
          </div>
        </section>

        <section className="space-y-2">
          <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
            Périmètres
          </h3>

          {changeable ? (
            <ScopePicker
              value={apiKey.scopes}
              onChange={(scopes) =>
                void onChangeScopes(apiKey.id, pruneCovered(scopes))
              }
            />
          ) : (
            <p className="text-sm text-slate-700">
              {apiKey.scopes.map(scopeLabel).join(", ")}
            </p>
          )}
        </section>

        {changeable && (
          <section className="space-y-2">
            <h3 className="border-b border-slate-200 pb-1.5 text-sm font-semibold text-slate-900">
              Révocation
            </h3>
            <p className="text-sm text-slate-500">
              Tout ce qui utilise cette clé cessera de fonctionner dès le prochain
              appel.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="cursor-pointer text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={() => setConfirming(true)}
            >
              Révoquer la clé
            </Button>
            <RevokeApiKeyDialog
              open={confirming}
              onOpenChange={setConfirming}
              name={apiKey.name}
              onConfirm={() => void onRevoke(apiKey.id)}
            />
          </section>
        )}
      </div>
    </SidePanel>
  );
}
