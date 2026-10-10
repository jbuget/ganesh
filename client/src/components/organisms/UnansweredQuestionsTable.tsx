"use client";

import { UnansweredQuestionRow } from "@/components/molecules/UnansweredQuestionRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { UnansweredQuestionResponse } from "@/lib/api/generated/model";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface UnansweredQuestionsTableProps {
  questions: UnansweredQuestionResponse[];
  askerName: (askerId: number) => string;
  onOpen: (questionId: number) => void;
}

/** The questions that came back with no answer, latest first. */
export function UnansweredQuestionsTable({
  questions,
  askerName,
  onOpen,
}: UnansweredQuestionsTableProps) {
  return (
    <div className="[&_[data-slot=table-container]]:overflow-visible">
      <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
        <TableHeader className={TABLE_HEADER}>
          <TableRow>
            <TableHead className={STRONG_SEPARATOR}>Question</TableHead>
            <TableHead>Personne</TableHead>
            <TableHead>Posée le</TableHead>
            <TableHead>Pourquoi</TableHead>
            <TableHead className="text-right">Lectures</TableHead>
            <TableHead className="text-right">Durée</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {questions.map((question) => (
            <UnansweredQuestionRow
              key={question.id}
              question={question}
              askerName={askerName(question.asker_id)}
              onOpen={() => onOpen(question.id)}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
