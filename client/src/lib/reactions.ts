import { Reaction } from "@/lib/api/generated/model";

/**
 * What each sign shows, and what it says.
 *
 * The API names the reactions and the interface draws them, as a phase is
 * named by the domain and coloured here. The order is the one the bar is drawn
 * in, and it is the order the API declares: a bar that reshuffled itself as
 * people reacted could not be read at a glance.
 */
export const REACTIONS: { reaction: Reaction; glyph: string; label: string }[] = [
  { reaction: Reaction.thumbs_up, glyph: "👍", label: "D'accord" },
  { reaction: Reaction.thumbs_down, glyph: "👎", label: "Pas d'accord" },
  { reaction: Reaction.laugh, glyph: "😄", label: "Ça me fait rire" },
  { reaction: Reaction.hooray, glyph: "🎉", label: "Bravo" },
  { reaction: Reaction.confused, glyph: "😕", label: "Ça m'interroge" },
  { reaction: Reaction.heart, glyph: "❤️", label: "J'aime" },
  { reaction: Reaction.rocket, glyph: "🚀", label: "En route" },
  { reaction: Reaction.eyes, glyph: "👀", label: "Je regarde" },
];

const BY_NAME = new Map(REACTIONS.map((one) => [one.reaction, one]));

/** The glyph a sign is drawn with. */
export function glyphOf(reaction: Reaction): string {
  return BY_NAME.get(reaction)?.glyph ?? "";
}

/** What a sign says, in French. */
export function labelOf(reaction: Reaction): string {
  return BY_NAME.get(reaction)?.label ?? "";
}

/**
 * Who left a sign, as one reads it out.
 *
 * Beyond four names the rest are counted: a tooltip listing a whole team stops
 * being read.
 */
export function whoReacted(people: string[]): string {
  if (people.length <= 4) {
    if (people.length <= 1) return people.join("");
    return `${people.slice(0, -1).join(", ")} et ${people[people.length - 1]}`;
  }
  const others = people.length - 4;
  return `${people.slice(0, 4).join(", ")} et ${others} autre${others > 1 ? "s" : ""}`;
}
