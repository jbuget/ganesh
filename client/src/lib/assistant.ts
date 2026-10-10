import { ApiError } from "@/lib/api/fetcher";

/** A project the answer was read from, named so a reader can go and check. */
export interface ConsultedProject {
  id: number;
  label: string;
}

const PROJECT_PAGE = /^\/projects\/(\d+)(?:\/|$)/;

/**
 * The project the person is looking at, if any.
 *
 * « Où en est-il ? » asked from a project is about that project. A panel open
 * over a screen wins over the page behind it: it is what the person is reading.
 */
export function projectInView(pathname: string, query: string): number | null {
  const panel = Number(new URLSearchParams(query).get("mission"));
  if (panel) return panel;
  const page = PROJECT_PAGE.exec(pathname);
  return page ? Number(page[1]) : null;
}

/** What the panel says when no answer came back. */
export function refusalOf(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 503) {
      return "L'assistant est indisponible pour le moment. Réessayez plus tard.";
    }
    if (error.status === 409) {
      return "Cette conversation est terminée. Commencez-en une nouvelle.";
    }
    if (error.status === 422) {
      return "Cette question ne peut pas être posée : elle est vide ou trop longue.";
    }
  }
  return "L'assistant n'a pas pu répondre.";
}

/**
 * The projects an answer was read from, named from the list the screen holds.
 *
 * One the list no longer names — deleted since — is left out: a link to it
 * would lead nowhere.
 */
export function consultedProjects(
  ids: number[],
  missions: { project: { id: number; label: string } }[],
): ConsultedProject[] {
  const labels = new Map(missions.map(({ project }) => [project.id, project.label]));
  return ids.flatMap((id) => {
    const label = labels.get(id);
    return label === undefined ? [] : [{ id, label }];
  });
}

/** What a project is matched by in an answer. */
interface NamedProject {
  id: number;
  label: string;
  kind: string;
}

/** What a person is matched by in an answer. */
interface NamedPerson {
  id: number;
  display_name: string;
  first_name?: string | null;
  last_name?: string | null;
}

/** Shorter than this, a label is a word before it is a name. */
const SHORTEST_NAME = 3;

/**
 * Where each name an answer may give leads.
 *
 * Read off the lists the screen already holds rather than asked of the model:
 * a name it forgot to mark would go unmarked, one it marked wrongly would lead
 * to the wrong sheet. Off-project work is left out — « Formation » and
 * « Support » are words of the language long before they are rows of the
 * reference list — and a project keeps its link should a person bear its name.
 */
export function nameTargets(
  projects: NamedProject[],
  people: NamedPerson[],
): Map<string, string> {
  const targets = new Map<string, string>();
  for (const person of people) {
    const civil = [person.first_name, person.last_name].filter(Boolean).join(" ");
    for (const name of [person.display_name, civil]) {
      if (name) targets.set(name, `/users?user=${person.id}`);
    }
  }
  for (const project of projects) {
    if (project.kind !== "off_project") {
      targets.set(project.label, `/projects/${project.id}`);
    }
  }
  for (const name of targets.keys()) {
    if (name.trim().length < SHORTEST_NAME) targets.delete(name);
  }
  return targets;
}

/** The little of the markdown tree the linking reads and writes. */
export interface MdNode {
  type: string;
  value?: string;
  url?: string;
  children?: MdNode[];
}

/** Nodes whose words are not to be linked: they are links, or code. */
const LEFT_ALONE = new Set(["link", "linkReference", "inlineCode", "code", "html"]);

/**
 * A remark plugin turning every name of `targets` into a link to it.
 *
 * It works on the parsed answer rather than on its source, so a name inside
 * code, inside a link or inside an address is never touched, and a label
 * carrying a bracket cannot break the markdown around it. Longest name first,
 * so « EDIT V2 » is not read as « EDIT » then « V2 », and whole words only.
 */
export function remarkNames(targets: Map<string, string>) {
  const names = [...targets.keys()].sort((a, b) => b.length - a.length);
  const pattern =
    names.length > 0
      ? new RegExp(
          `(?<![\\p{L}\\p{N}])(${names.map(escaped).join("|")})(?![\\p{L}\\p{N}])`,
          "gu",
        )
      : null;

  function split(text: string): MdNode[] {
    if (!pattern) return [{ type: "text", value: text }];
    const nodes: MdNode[] = [];
    let from = 0;
    for (const match of text.matchAll(pattern)) {
      if (match.index > from) {
        nodes.push({ type: "text", value: text.slice(from, match.index) });
      }
      nodes.push({
        type: "link",
        url: targets.get(match[0]),
        children: [{ type: "text", value: match[0] }],
      });
      from = match.index + match[0].length;
    }
    if (from < text.length) nodes.push({ type: "text", value: text.slice(from) });
    return nodes;
  }

  function visit(node: MdNode) {
    if (!node.children || LEFT_ALONE.has(node.type)) return;
    node.children = node.children.flatMap((child) => {
      if (child.type === "text" && child.value) return split(child.value);
      visit(child);
      return [child];
    });
  }

  return () => (tree: MdNode) => visit(tree);
}

function escaped(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
