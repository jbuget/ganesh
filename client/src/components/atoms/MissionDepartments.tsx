import type { Department } from "@/lib/api/generated/model";
import { departmentLabel } from "@/lib/departments";

interface MissionDepartmentsProps {
  departments: Department[];
}

/**
 * The departments a mission serves, as the picker writes them.
 *
 * One chip, then a count: the names run long — « Marketing, Communication &
 * RSE » — and two of them side by side in one column would each be truncated
 * to nothing. The first reads in full, the rest are counted and named on
 * hover, the way the links column does it.
 *
 * A mission serving nobody in particular leaves the cell empty: only what can
 * be read belongs in a table.
 */
export function MissionDepartments({ departments }: MissionDepartmentsProps) {
  if (departments.length === 0) return null;

  const [first, ...rest] = departments;

  return (
    <span
      className="flex items-center gap-1"
      title={departments.map(departmentLabel).join("\n")}
    >
      <span className="truncate rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700">
        {departmentLabel(first)}
      </span>
      {rest.length > 0 && (
        <span className="shrink-0 text-xs text-slate-400">+{rest.length}</span>
      )}
    </span>
  );
}
