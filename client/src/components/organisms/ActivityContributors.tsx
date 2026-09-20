"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ContributorResponse } from "@/lib/api/generated/model";
import { formatDays } from "@/lib/activity";
import { NOTHING, formatPersonDays, formatShare } from "@/lib/statistics";
import { STRONG_SEPARATOR, TABLE_FRAME, TABLE_HEADER } from "@/lib/table-frame";

interface ActivityContributorsProps {
  contributors: ContributorResponse[];
}

/**
 * What each person declared over the window, against what was expected.
 *
 * What was expected never leaves what was declared: five days read alone
 * says nothing about whether someone is part time, on leave, or simply late
 * in filling in their month. The coverage is read as a completeness of the
 * entry, never as a measure of the person — there is no ranking here, and
 * adding one would turn the whole product into something else.
 */
export function ActivityContributors({ contributors }: ActivityContributorsProps) {
  return (
    <section>
      <h2 className="mb-2 text-sm font-semibold text-slate-900">Par personne</h2>
      <p className="mb-3 text-sm text-slate-500">
        Ce que chacun a déclaré sur la période, au regard de ce qui était attendu. La
        couverture mesure la complétude de la saisie, pas le travail fourni.
      </p>

      <div className="[&_[data-slot=table-container]]:overflow-visible">
        <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
          <TableHeader className={TABLE_HEADER}>
            <TableRow>
              <TableHead className={STRONG_SEPARATOR}>Personne</TableHead>
              <TableHead className="text-right">Déclaré</TableHead>
              <TableHead className="text-right">Attendu</TableHead>
              <TableHead className="text-right">Couverture</TableHead>
              <TableHead className="text-right">Projets</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {contributors.map((someone) => (
              <TableRow key={someone.id} className="bg-slate-50 hover:bg-slate-100">
                <TableCell
                  className={`bg-white font-medium group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
                >
                  {someone.display_name}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatDays(someone.declared_days)}
                </TableCell>
                <TableCell className="text-right tabular-nums text-slate-500">
                  {formatPersonDays(someone.expected_days)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatShare(someone.coverage)}
                </TableCell>
                <TableCell className="text-right tabular-nums text-slate-500">
                  {someone.missions === 0 ? NOTHING : someone.missions}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
