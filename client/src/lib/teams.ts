import type { Department, Team } from "@/lib/api/generated/model";
import { departmentLabel } from "@/lib/departments";

/**
 * The teams a department is cut into, department by department.
 *
 * Only the departments that have said how they are divided appear: nothing is
 * supposed of the others. The API holds the same list and refuses a team
 * outside its department — this one only decides what the picker offers.
 */
export const TEAMS: { value: Team; label: string; department: Department }[] = [
  { value: "engineering", label: "Engineering", department: "information_systems" },
  { value: "data", label: "Data", department: "information_systems" },
  { value: "sysnet", label: "Sysnet", department: "information_systems" },
];

const BY_VALUE = new Map(TEAMS.map((team) => [team.value, team]));

/**
 * The teams of `department`, alphabetically: a list of names with no rank
 * between them is read by the alphabet, whatever order they were declared in.
 */
export function teamsOf(
  department: Department | null | undefined,
): { value: Team; label: string }[] {
  return TEAMS.filter((team) => team.department === department).sort((a, b) =>
    a.label.localeCompare(b.label, "fr"),
  );
}

export function teamLabel(value: Team): string {
  return BY_VALUE.get(value)?.label ?? value;
}

/**
 * The team that survives a change of department: kept while the new one still
 * holds it, let go otherwise — the API would refuse the pair.
 */
export function keptTeam(
  team: Team | null | undefined,
  department: Department | null | undefined,
): Team | null {
  if (!team) return null;
  return BY_VALUE.get(team)?.department === department ? team : null;
}

/** « Système d'information · Data », or the department alone, or nothing. */
export function workplaceLabel(
  department: Department | null | undefined,
  team: Team | null | undefined,
): string | null {
  if (!department) return null;
  const name = departmentLabel(department);
  return team ? `${name} · ${teamLabel(team)}` : name;
}
