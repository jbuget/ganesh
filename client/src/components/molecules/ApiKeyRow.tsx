import { ApiKeyStateBadge } from "@/components/atoms/ApiKeyStateBadge";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ApiKeyResponse } from "@/lib/api/generated/model";
import { isUsable, scopeLabel } from "@/lib/api-keys";
import { formatSpelledDate } from "@/lib/dates";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface ApiKeyRowProps {
  apiKey: ApiKeyResponse;
  onOpen: () => void;
}

/** A date, or a dash where there is nothing to say. */
function Day({ iso }: { iso: string | null }) {
  if (iso === null) return <span className="text-slate-400">—</span>;
  return <span className="text-slate-700">{formatSpelledDate(iso)}</span>;
}

/**
 * One service account in the table.
 *
 * The whole row opens the panel beside the list, as a teammate's does: what
 * one does to a key is done there, not from a button hidden at the end of a
 * line.
 *
 * A key that no longer opens anything is dimmed rather than hidden: the audit
 * refers to it, and « revoked three months ago » is an answer the table owes
 * whoever comes looking.
 */
export function ApiKeyRow({ apiKey, onOpen }: ApiKeyRowProps) {
  const spent = !isUsable(apiKey);

  return (
    // The row takes the page background, the name cell white: the key reads as
    // the anchor of the line rather than as its first column. The same grammar
    // as the teammates table.
    <TableRow
      onClick={onOpen}
      className={`group cursor-pointer bg-slate-50 hover:bg-slate-100 ${
        spent ? "text-slate-400" : ""
      }`}
    >
      <TableCell
        className={`bg-white py-2 group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
      >
        <span className="font-medium text-slate-900">{apiKey.name}</span>
        <code className="mt-0.5 block font-mono text-xs text-slate-500">
          {apiKey.masked}
        </code>
      </TableCell>

      <TableCell className="py-2">
        <span className="text-slate-700">
          {apiKey.scopes.map(scopeLabel).join(", ")}
        </span>
      </TableCell>

      <TableCell className="py-2">
        <span className="text-slate-700">{apiKey.owner.display_name}</span>
      </TableCell>

      <TableCell className="py-2">
        <Day iso={apiKey.last_used_at} />
      </TableCell>

      <TableCell className="py-2">
        <Day iso={apiKey.expires_at} />
      </TableCell>

      <TableCell className="py-2">
        <ApiKeyStateBadge state={apiKey.state} />
      </TableCell>
    </TableRow>
  );
}
