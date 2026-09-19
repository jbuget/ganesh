"use client";

import { useState } from "react";

import { TeammateSelector } from "@/components/atoms/TeammateSelector";
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
import type { ApiKeyScope, UserResponse } from "@/lib/api/generated/model";
import {
  SCOPES,
  coveredBy,
  oneYearFromNow,
  pruneCovered,
  scopeLabel,
} from "@/lib/api-keys";

interface CreateApiKeyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  teammates: UserResponse[];
  onCreate: (fields: {
    name: string;
    owner_id: number;
    scopes: ApiKeyScope[];
    expires_at: string | null;
  }) => Promise<void>;
}

/**
 * Minting a service account.
 *
 * Four questions, and each one is asked because the answer matters later: the
 * name is read by the whole team, the owner is who answers for the machine,
 * the scopes are the only thing the key will ever open, and the expiry is
 * offered rather than imposed — a key that never expires stays possible, but
 * it becomes a choice one makes on purpose.
 */
export function CreateApiKeyDialog({
  open,
  onOpenChange,
  teammates,
  onCreate,
}: CreateApiKeyDialogProps) {
  const [name, setName] = useState("");
  const [ownerId, setOwnerId] = useState<number | null>(null);
  const [scopes, setScopes] = useState<ApiKeyScope[]>([]);
  const [expiresAt, setExpiresAt] = useState<string>(oneYearFromNow());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const complete = name.trim() !== "" && ownerId !== null && scopes.length > 0;

  function reset() {
    setName("");
    setOwnerId(null);
    setScopes([]);
    setExpiresAt(oneYearFromNow());
    setError(null);
  }

  function toggleScope(scope: ApiKeyScope) {
    setScopes((current) =>
      current.includes(scope)
        ? current.filter((kept) => kept !== scope)
        : [...current, scope],
    );
  }

  async function submit() {
    if (!complete || ownerId === null) return;
    setBusy(true);
    setError(null);
    try {
      await onCreate({
        name: name.trim(),
        owner_id: ownerId,
        // Only what the server needs: it derives the rest from the broad ones.
        scopes: pruneCovered(scopes),
        expires_at: expiresAt || null,
      });
      onOpenChange(false);
      reset();
    } catch {
      setError("La création a échoué. Réessayez.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) reset();
      }}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nouvelle clé d&apos;API</DialogTitle>
          <DialogDescription>
            Une clé appartient à une machine, jamais à une personne. Elle n&apos;ouvre
            que les périmètres cochés ici.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="api-key-name">Nom</Label>
            <Input
              id="api-key-name"
              value={name}
              placeholder="CI waat-tools"
              onChange={(event) => setName(event.target.value)}
            />
            {/* Strangers read this table: the name is written for them. */}
            <p className="text-xs text-slate-500">
              Lu par toute l&apos;équipe : dites quelle machine s&apos;en sert.
            </p>
          </div>

          <div className="space-y-1.5">
            {/* The same control as the activity screen, search included: a
                team of twenty is found by typing three letters. */}
            <TeammateSelector
              stacked
              id="api-key-owner"
              label="Compte associé"
              teammates={teammates}
              selectedId={ownerId}
              onSelect={setOwnerId}
            />
            <p className="text-xs text-slate-500">
              Qui répond de ce que fait cette machine. La clé cesse de fonctionner si ce
              compte est désactivé.
            </p>
          </div>

          <fieldset className="space-y-1.5">
            <legend className="text-sm font-medium">Périmètres</legend>
            <div className="space-y-1.5">
              {SCOPES.map((scope) => {
                // A broad scope ticks and locks what it carries: the reach of
                // « Tous » is seen where it is decided, not discovered later.
                const covering = coveredBy(scope.value, scopes);
                return (
                  <label
                    key={scope.value}
                    className={[
                      "flex items-start gap-2 text-sm",
                      covering ? "cursor-default" : "cursor-pointer",
                    ].join(" ")}
                  >
                    <input
                      type="checkbox"
                      checked={covering !== null || scopes.includes(scope.value)}
                      disabled={covering !== null}
                      onChange={() => toggleScope(scope.value)}
                      className="mt-0.5 size-4 rounded border-slate-300 enabled:cursor-pointer disabled:cursor-default"
                    />
                    <span className={covering ? "opacity-50" : undefined}>
                      <span className="text-slate-800">{scope.label}</span>
                      <span className="block text-xs text-slate-500">
                        {covering
                          ? `Inclus dans « ${scopeLabel(covering)} »`
                          : scope.hint}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div className="space-y-1.5">
            <Label htmlFor="api-key-expiry">Expiration</Label>
            <Input
              id="api-key-expiry"
              type="date"
              value={expiresAt}
              onChange={(event) => setExpiresAt(event.target.value)}
            />
            <p className="text-xs text-slate-500">
              Un an par défaut. Vider le champ crée une clé sans expiration.
            </p>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            className="cursor-pointer"
            onClick={() => onOpenChange(false)}
          >
            Annuler
          </Button>
          <Button
            className="cursor-pointer"
            disabled={!complete || busy}
            onClick={() => void submit()}
          >
            Créer la clé
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
