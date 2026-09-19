"use client";

import { useState } from "react";

import { ApiKeyStateBadge } from "@/components/atoms/ApiKeyStateBadge";
import { RevokeApiKeyDialog } from "@/components/atoms/RevokeApiKeyDialog";
import { Button } from "@/components/ui/button";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ApiKeyResponse } from "@/lib/api/generated/model";
import { isUsable, scopeLabel } from "@/lib/api-keys";
import { formatSpelledDate } from "@/lib/dates";

interface ApiKeyRowProps {
  apiKey: ApiKeyResponse;
  /** Only a manager cuts a key. The server refuses anyone else regardless. */
  canRevoke: boolean;
  onRevoke: (keyId: number) => void | Promise<void>;
}

/** A date, or a dash where there is nothing to say. */
function Day({ iso }: { iso: string | null }) {
  if (iso === null) return <span className="text-slate-400">—</span>;
  return <span className="text-slate-700">{formatSpelledDate(iso)}</span>;
}

/**
 * One service account in the table.
 *
 * A key that no longer opens anything is dimmed rather than hidden: the audit
 * refers to it, and « revoked three months ago » is an answer the table owes
 * whoever comes looking.
 */
export function ApiKeyRow({ apiKey, canRevoke, onRevoke }: ApiKeyRowProps) {
  const [confirming, setConfirming] = useState(false);
  const spent = !isUsable(apiKey);

  return (
    <TableRow className={spent ? "text-slate-400" : undefined}>
      <TableCell>
        <span className="font-medium text-slate-900">{apiKey.name}</span>
        <code className="mt-0.5 block font-mono text-xs text-slate-500">
          {apiKey.masked}
        </code>
      </TableCell>

      <TableCell>
        <span className="text-slate-700">
          {apiKey.scopes.map(scopeLabel).join(", ")}
        </span>
      </TableCell>

      <TableCell>
        <span className="text-slate-700">{apiKey.owner.display_name}</span>
      </TableCell>

      <TableCell>
        <Day iso={apiKey.last_used_at} />
      </TableCell>

      <TableCell>
        <Day iso={apiKey.expires_at} />
      </TableCell>

      <TableCell>
        <ApiKeyStateBadge state={apiKey.state} />
      </TableCell>

      <TableCell className="text-right">
        {canRevoke && isUsable(apiKey) && (
          <>
            <Button
              size="sm"
              variant="ghost"
              className="cursor-pointer text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={() => setConfirming(true)}
            >
              Révoquer
            </Button>
            <RevokeApiKeyDialog
              open={confirming}
              onOpenChange={setConfirming}
              name={apiKey.name}
              onConfirm={() => void onRevoke(apiKey.id)}
            />
          </>
        )}
      </TableCell>
    </TableRow>
  );
}
