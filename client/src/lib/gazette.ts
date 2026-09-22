/**
 * La Gazette, said in French.
 *
 * The server hands over facts in the vocabulary of the domain — `went_live`,
 * `phase_stepped_back` — and never in the one the reader uses. Turning the one
 * into the other happens here rather than in the component, so that every
 * wording is under test: a digest that reads « project_archived » says nothing
 * to whoever opens it.
 *
 * The chapeau is the one piece of French the API carries, because a model
 * wrote it.
 */
import type {
  ChapterResponse,
  DigestResponse,
  HighlightResponse,
  MovementResponse,
  TallyResponse,
} from "@/lib/api/generated/model";
import { phaseLabel } from "@/lib/board";

/**
 * A project's name, ready to have a verb put after it.
 *
 * Several labels were typed with a full stop at the end — they were written
 * as sentences. Left on, the gazette reads « … dans les PDF. a été archivé ».
 * The stop is the label's, not the sentence's: it goes wherever we are the
 * ones building the sentence.
 *
 * It is applied to missions alone. A person's name is left exactly as it was
 * given, whatever it ends with.
 */
export function missionName(label: string): string {
  return label.replace(/[.\s]+$/, "") || label;
}

/** One movement of the month, said in French. */
export function movementSentence(movement: MovementResponse): string {
  const subject = subjectOf(movement);
  // The news is what happened; the project is where it landed. Turning it
  // round — « Ganesh a reçu une actualité » — is not how anyone says it.
  if (movement.kind === "news_posted") {
    return `Une actualité a été publiée sur ${subject}`;
  }
  return `${subject} ${movementPredicate(movement)}`;
}

/**
 * The same fact with its subject left off, for a line read under a heading
 * that already names it.
 *
 * « WAATcher est passé en exploitation » under a heading reading « WAATcher »
 * says it twice; the predicate alone reads as the chronicle it is.
 */
export function movementPredicate(movement: MovementResponse): string {
  switch (movement.kind) {
    case "project_created":
      return "a rejoint la liste des projets";
    case "project_archived":
      return "a été archivé";
    case "project_revived":
      return "est revenu dans la liste des projets";
    case "went_live":
      return "est passé en exploitation";
    case "phase_advanced":
      return `est passé ${phaseMove(movement)}`;
    case "phase_stepped_back":
      return `est revenu ${phaseMove(movement)}`;
    case "news_posted":
      return "une actualité a été publiée";
    // A need is feminine — « une demande » — and every one of these agrees
    // with it. Nothing but opening the screen catches a « a été accepté ».
    case "request_filed":
      return "a été déposée";
    case "request_accepted":
      return "a été acceptée";
    case "request_rejected":
      return "a été refusée";
    case "request_deferred":
      return "a été reportée à plus tard";
    case "request_converted":
      return "est devenue un projet";
    case "teammate_joined":
      return "a rejoint l'équipe";
    case "teammate_returned":
      // « est revenue » for half the team, and the application holds no
      // gender — rightly. « de retour » agrees with nobody.
      return "est de retour dans l'équipe";
    case "teammate_left":
      return "a quitté l'équipe";
    default:
      return "";
  }
}

function subjectOf(movement: MovementResponse): string {
  return movement.project_id === null
    ? movement.subject
    : missionName(movement.subject);
}

/**
 * Where a phase came from and went, when the register says both.
 *
 * A move it only knows one end of reads « en Développement »: naming a phase
 * it never recorded would be inventing one.
 */
function phaseMove(movement: MovementResponse): string {
  const to = movement.to_status ? phaseLabel(movement.to_status) : null;
  if (!to) return "de phase";
  if (!movement.from_status) return `en ${to}`;
  return `${from_(phaseLabel(movement.from_status))} à ${to}`;
}

/**
 * « de Cadrage », but « d'Exploitation ».
 *
 * Elision is invisible to the type checker and to any test asserting on a
 * count: two of the six phases begin with a vowel, and « de Exploitation »
 * only ever shows up by opening the screen.
 */
function from_(phase: string): string {
  return /^[aeiouâéêèîôûAEIOUÂÉÊÈÎÔÛ]/.test(phase) ? `d'${phase}` : `de ${phase}`;
}

/** One fact worth reading twice, said in French. */
export function highlightSentence(highlight: HighlightResponse): string {
  const subject =
    highlight.project_id === null ? highlight.label : missionName(highlight.label);

  switch (highlight.kind) {
    case "went_live":
      return `${subject} est passé en exploitation`;
    case "phase_stepped_back":
      return `${subject} est revenu à une phase antérieure`;
    case "archived_before_delivery":
      return `${subject} a été archivé sans avoir été mis en service`;
    case "go_live_overdue":
      return `${subject} a dépassé sa date de mise en service annoncée`;
    case "teammate_joined":
      return `${subject} a rejoint l'équipe`;
    case "teammate_returned":
      return `${subject} est de retour dans l'équipe`;
    case "teammate_left":
      return `${subject} a quitté l'équipe`;
    default:
      return subject;
  }
}

/** One piece of the chapeau: a project's name, or plain prose around it. */
export interface ProseSegment {
  text: string;
  isProject: boolean;
}

/**
 * One line of a chapter's chronicle.
 *
 * The heading names the project, so a line about the project itself does not
 * repeat it. A line about one of its work packages does: under « WAATcher »,
 * « Lot API a été archivé » is the only way to know which lot moved.
 *
 * The chapter about no project names every subject: what its heading says is
 * « L'équipe », which identifies nobody.
 */
export function chapterLine(
  movement: MovementResponse,
  chapter: ChapterResponse,
): string {
  const isTheChapterItself =
    chapter.project_id !== null && movement.project_id === chapter.project_id;
  return isTheChapterItself ? movementPredicate(movement) : movementSentence(movement);
}

/**
 * What a chapter is called on screen.
 *
 * A chapter about no mission is named here rather than by the server: the
 * domain says « this is about no mission », and saying it in French is the
 * interface's business.
 */
/**
 * What tells one chapter from another.
 *
 * The project's id will not do on its own: two chapters carry none — the
 * needs and the team — and keying both on nothing made them one. They opened
 * and closed together, and React was told of two children sharing a key.
 */
export function chapterKey(chapter: ChapterResponse): string {
  return chapter.of === "project" ? `project:${chapter.project_id}` : chapter.of;
}

export function chapterTitle(chapter: ChapterResponse): string {
  if (chapter.of === "requests") return "Les demandes";
  if (chapter.of === "team") return "L'équipe";
  return chapter.label === null ? "L'équipe" : missionName(chapter.label);
}

/** Every project a chapter names: its own, and those of its packages. */
function namesIn(chapter: ChapterResponse): string[] {
  // A chapter about no project names none: what it holds are needs, or
  // people, and neither is a mission the chapeau may lean on.
  if (chapter.of !== "project") return [];
  const own = chapter.label === null ? [] : [chapter.label];
  const packages = chapter.movements
    .filter((movement) => movement.project_id !== chapter.project_id)
    .map((movement) => movement.subject);
  return [...own, ...packages];
}

/**
 * The projects a digest names, as the register spells them.
 *
 * Read from the facts rather than from the reference list: a digest is an
 * archive, and it must go on naming what it named the day it was generated,
 * whatever has been renamed since.
 */
export function projectLabels(digest: DigestResponse): string[] {
  return [
    ...new Set([
      ...digest.chapters.flatMap(namesIn),
      ...digest.highlights
        .filter((highlight) => highlight.project_id !== null)
        .map((highlight) => highlight.label),
    ]),
  ];
}

/**
 * The chapeau, cut so that the projects it names can be set apart.
 *
 * The emphasis is put on at the last moment, here, and never asked of the
 * model: a model told to write markup writes markup wherever it feels like
 * it, and the one rule the chapeau must obey — no figures — is hard enough to
 * hold without also policing asterisks.
 *
 * Only a name the digest actually carries is set apart, and only where it
 * appears word for word. A model that rearranges a label — « le SFTP de WAAT
 * / Suez » for « WAAT / Suez - SFTP » — leaves that sentence plain, which is
 * the right way round: emphasis is a claim that this is the project, and a
 * claim is not something to guess at.
 */
export function emphasiseProjects(prose: string, labels: string[]): ProseSegment[] {
  const names = recognisable(labels);
  if (names.length === 0) return [{ text: prose, isProject: false }];

  // Split on a capturing group: the pieces then alternate prose, name, prose.
  const pattern = new RegExp(`(${names.map(escaped).join("|")})`, "gi");
  return prose
    .split(pattern)
    .map((text, rank) => ({ text, isProject: rank % 2 === 1 }))
    .filter((segment) => segment.text !== "");
}

/**
 * The forms of a label worth looking for, longest first.
 *
 * Longest first so that a project whose name opens another's — « RAGGAE » and
 * « RAGGAE- AssistantStudio » — does not steal the longer one's emphasis. A
 * label ending in a full stop is also looked for without it: several do, and
 * the model drops it when the sentence carries on.
 */
function recognisable(labels: string[]): string[] {
  return [
    ...new Set(labels.flatMap((label) => [label, missionName(label)]).filter(Boolean)),
  ].sort((a, b) => b.length - a.length);
}

function escaped(label: string): string {
  return label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** What each side of the highlights is called on screen. */
export const TONE_TITLES = {
  notable: "Faits marquants",
  attention: "Points d'attention",
} as const;

/** One figure of the month, named. */
export interface TallyLine {
  label: string;
  value: number;
}

/**
 * What the month came to, in the order a reader takes it in.
 *
 * Agreement is written out rather than computed from the figure: « projet
 * créé » and « projets créés » are invisible to the type checker, and a test
 * asserting on a count would never catch the wrong one.
 */
export function tallyLines(tally: TallyResponse): TallyLine[] {
  return [
    line(tally.projects_created, "projet créé", "projets créés"),
    line(tally.projects_archived, "projet archivé", "projets archivés"),
    line(tally.phase_changes, "changement de phase", "changements de phase"),
    line(tally.news_posted, "actualité publiée", "actualités publiées"),
    line(tally.months_validated, "mois validé", "mois validés"),
    line(tally.requests_filed, "demande déposée", "demandes déposées"),
    line(
      tally.requests_converted,
      "demande devenue un projet",
      "demandes devenues des projets",
    ),
  ];
}

function line(value: number, one: string, many: string): TallyLine {
  return { label: value > 1 ? many : one, value };
}

/** Whether a month left anything at all in the register. */
export function isQuietMonth(digest: DigestResponse): boolean {
  return digest.chapters.length === 0 && digest.highlights.length === 0;
}

/**
 * How a version is offered in the picker.
 *
 * The date is what tells two versions apart — the number alone says which came
 * first, not what either was read on.
 */
export function versionLabel(version: number, generatedAt: string): string {
  return `Version ${version} — ${formatGeneratedAt(generatedAt)}`;
}

/** When a digest was asked for, to the minute: two can share a day. */
export function formatGeneratedAt(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
