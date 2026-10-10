import type {
  Cause,
  Judgement,
  ReadAssistantIndicatorsParams,
} from "@/lib/api/generated/model";

/**
 * What an administrator narrowed the exchanges down to.
 *
 * The same four criteria read the list, the indicators and the export, so
 * that a figure on screen and the file one saves next to it never disagree.
 */
export interface StudyFilters {
  /** Whose questions, by id. One at a time; empty is everyone's. */
  askerIds: string[];
  judgement: Judgement | "";
  /** Days, both included. Empty is « since always » and « until now ». */
  fromDay: string;
  toDay: string;
}

export const NO_STUDY_FILTER: StudyFilters = {
  askerIds: [],
  judgement: "",
  fromDay: "",
  toDay: "",
};

export function hasStudyFilter(filters: StudyFilters): boolean {
  return (
    filters.askerIds.length > 0 ||
    filters.judgement !== "" ||
    filters.fromDay !== "" ||
    filters.toDay !== ""
  );
}

/** An empty criterion is left out rather than sent empty. */
export function asStudyQuery(filters: StudyFilters): ReadAssistantIndicatorsParams {
  const query: ReadAssistantIndicatorsParams = {};
  if (filters.askerIds.length > 0) query.asker_id = Number(filters.askerIds[0]);
  if (filters.judgement !== "") query.judgement = filters.judgement;
  if (filters.fromDay !== "") query.from_day = filters.fromDay;
  if (filters.toDay !== "") query.to_day = filters.toDay;
  return query;
}

/**
 * Why an answer came out as it did, as the one annotating it says.
 *
 * The first two are the point of keeping what the tools read: a wrong answer
 * is fixed in a tool or in the prompt, and telling which is the whole study.
 */
export const CAUSES: { value: Cause; label: string; detail: string }[] = [
  {
    value: "wrong_reading",
    label: "Lecture fausse",
    detail: "Un outil a mal lu le registre, ou trop peu.",
  },
  {
    value: "wrong_phrasing",
    label: "Phrase fausse",
    detail: "Les lectures étaient justes, le modèle les a mal tournées.",
  },
  {
    value: "out_of_scope",
    label: "Hors champ",
    detail: "Aucun outil ne tient ce qui était demandé.",
  },
  {
    value: "right_answer",
    label: "Bonne réponse",
    detail: "Rien à corriger.",
  },
];

export function causeLabel(cause: Cause): string {
  return CAUSES.find((held) => held.value === cause)?.label ?? cause;
}

export const JUDGEMENTS: { value: Judgement; label: string }[] = [
  { value: "helpful", label: "Utile" },
  { value: "unhelpful", label: "Pas utile" },
  { value: "unjudged", label: "Sans avis" },
];

const ONE_DECIMAL = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/** A wait, in seconds: « 5,2 s ». A dash where nobody waited. */
export function seconds(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  return `${ONE_DECIMAL.format(ms / 1000)} s`;
}

/** A share of a whole, as a percentage: « 33 % ». A dash for a share of nothing. */
export function share(part: number, whole: number): string {
  if (whole === 0) return "—";
  return `${Math.round((part / whole) * 100)} %`;
}

const THOUSANDS = new Intl.NumberFormat("fr-FR");

/** « 12 480 », spaced the French way. */
export function count(value: number): string {
  return THOUSANDS.format(value);
}
