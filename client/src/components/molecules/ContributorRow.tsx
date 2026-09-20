"use client";

import { ContributorMissions } from "@/components/atoms/ContributorMissions";
import { TableCell, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { ContributorResponse } from "@/lib/api/generated/model";
import type { MissionShare } from "@/lib/activity";
import { formatDays } from "@/lib/activity";
import { NOTHING, formatPersonDays, formatShare } from "@/lib/statistics";
import { STRONG_SEPARATOR } from "@/lib/table-frame";

interface ContributorRowProps {
  contributor: ContributorResponse;
  /** What they put time on, ready to break the row's total down. */
  missions: MissionShare[];
}

/**
 * One person over the window: what they declared, against what was expected.
 *
 * The whole row opens the breakdown, not just the name — a row is what one
 * aims at, and a name is a small target among four columns of figures. It
 * carries `tabIndex` so the detail is reachable from the keyboard, and
 * `cursor-help` rather than a pointer: there is nothing to click here, only
 * something to read.
 */
export function ContributorRow({ contributor, missions }: ContributorRowProps) {
  return (
    <Tooltip trackCursorAxis="both">
      <TooltipTrigger
        render={
          <TableRow
            tabIndex={0}
            className="cursor-help bg-slate-50 hover:bg-slate-100 focus-visible:bg-slate-100 focus-visible:outline-none"
          />
        }
      >
        <TableCell
          className={`bg-white font-medium group-hover:bg-slate-50 ${STRONG_SEPARATOR}`}
        >
          {contributor.display_name}
        </TableCell>
        <TableCell className="text-right tabular-nums">
          {formatDays(contributor.declared_days)}
        </TableCell>
        <TableCell className="text-right tabular-nums text-slate-500">
          {formatPersonDays(contributor.expected_days)}
        </TableCell>
        <TableCell className="text-right tabular-nums">
          {formatShare(contributor.coverage)}
        </TableCell>
        <TableCell className="text-right tabular-nums text-slate-500">
          {contributor.missions === 0 ? NOTHING : contributor.missions}
        </TableCell>
      </TooltipTrigger>

      <TooltipContent align="start">
        <ContributorMissions
          missions={missions}
          declaredDays={contributor.declared_days}
        />
      </TooltipContent>
    </Tooltip>
  );
}
