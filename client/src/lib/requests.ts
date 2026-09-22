import type { RequestResponse, RequestState } from "@/lib/api/generated/model";

/**
 * Where a need stands, said in French.
 *
 * The API names a state in the domain's vocabulary — `deferred`, `converted` —
 * and the reader gets it here, as the audit log and the inbox already work.
 * Under test: a state nobody can read is not one.
 *
 * The dot follows the road, from the grey of what is still being written to
 * the green of what became a project. Refused is the one that leaves it.
 */
export const REQUEST_STATES: {
  value: RequestState;
  label: string;
  dot: string;
}[] = [
  { value: "draft", label: "Brouillon", dot: "bg-slate-300" },
  { value: "submitted", label: "Soumise", dot: "bg-blue-500" },
  { value: "deferred", label: "Plus tard", dot: "bg-amber-500" },
  { value: "rejected", label: "Refusée", dot: "bg-rose-500" },
  { value: "accepted", label: "Acceptée", dot: "bg-teal-500" },
  { value: "converted", label: "Convertie", dot: "bg-emerald-500" },
];

const BY_VALUE = new Map(REQUEST_STATES.map((state) => [state.value, state]));

export function requestStateLabel(value: RequestState): string {
  return BY_VALUE.get(value)?.label ?? value;
}

export function requestStateDot(value: RequestState): string {
  return BY_VALUE.get(value)?.dot ?? "bg-slate-300";
}

/**
 * What a request still needs before it may be handed over.
 *
 * The same three the API demands. Said here so the button says why it is
 * disabled rather than leaving the reader to guess, and the server refuses
 * all the same: this is a courtesy, never the rule.
 */
export function missingBeforeSubmitting(request: RequestResponse): string[] {
  const missing: string[] = [];
  if (!request.problem?.trim()) missing.push("le problème");
  if (!request.impact?.trim()) missing.push("qui est concerné");
  if (!request.expected_outcome?.trim()) missing.push("le résultat attendu");
  return missing;
}

/** « le problème et qui est concerné » — what is still missing, in a sentence. */
export function sayMissing(missing: string[]): string {
  if (missing.length === 0) return "";
  if (missing.length === 1) return missing[0];
  return `${missing.slice(0, -1).join(", ")} et ${missing[missing.length - 1]}`;
}
