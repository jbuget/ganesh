"use client";

import { AssistantConversationRow } from "@/components/molecules/AssistantConversationRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ConversationSummaryResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface AssistantConversationsTableProps {
  conversations: ConversationSummaryResponse[];
  askerName: (askerId: number) => string;
  onOpen: (conversationId: string) => void;
}

/** Everybody's conversations with the assistant, latest first. */
export function AssistantConversationsTable({
  conversations,
  askerName,
  onOpen,
}: AssistantConversationsTableProps) {
  return (
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={STRONG_SEPARATOR}>Première question</TableHead>
            <TableHead>Personne</TableHead>
            <TableHead>Dernière question</TableHead>
            <TableHead className="text-right">Échanges</TableHead>
            <TableHead>Avis</TableHead>
            <TableHead>Annotés</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {conversations.map((conversation) => (
            <AssistantConversationRow
              key={conversation.id}
              conversation={conversation}
              askerName={askerName(conversation.asker_id)}
              onOpen={() => onOpen(conversation.id)}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
