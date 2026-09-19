"use client";

import { ApiKeyRow } from "@/components/molecules/ApiKeyRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ApiKeyResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface ApiKeysTableProps {
  /** The keys to draw, already in order. */
  keys: ApiKeyResponse[];
  /** Only a manager cuts a key. The server refuses anyone else regardless. */
  canRevoke: boolean;
  onRevoke: (keyId: number) => void | Promise<void>;
}

/**
 * The service accounts as a table: what each one opens, who answers for it,
 * and when it was last used.
 *
 * It draws what it is given and asks for the rest: no criteria of its own, no
 * fetching, no opinion on what to say when there is nothing — the screen
 * around it answers that, in its own words.
 *
 * It reads under the same frame as the teammates and the mission reference
 * list: a strong rule around, a strong rule under the titles, and the column
 * that names the key closed off from those that describe it.
 */
export function ApiKeysTable({ keys, canRevoke, onRevoke }: ApiKeysTableProps) {
  return (
    // The shadcn container opens a scrolling context that would hold the header
    // inside the table: we neutralise it so the `sticky` latches onto the
    // page's scrolling area.
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={STRONG_SEPARATOR}>Clé</TableHead>
            <TableHead>Périmètres</TableHead>
            <TableHead>Compte associé</TableHead>
            <TableHead>Dernière utilisation</TableHead>
            <TableHead>Expiration</TableHead>
            <TableHead>État</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>

        <TableBody>
          {keys.map((apiKey) => (
            <ApiKeyRow
              key={apiKey.id}
              apiKey={apiKey}
              canRevoke={canRevoke}
              onRevoke={onRevoke}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
