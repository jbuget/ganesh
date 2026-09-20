/**
 * How a message names someone.
 *
 * A mention travels as a markdown link — `@[Nom](mention://user/12)` — and
 * points at the person by **id**, never by name: a name changes with a
 * marriage or a typo fixed, and a mention read back from the text would then
 * name somebody who no longer exists.
 *
 * The same shape is read server-side, in
 * `projects/domain/services/mentions.py`: it is what decides who is told they
 * were spoken to. The two must stay in step.
 */

/** Someone a message may name. */
export interface MentionablePerson {
  id: number;
  display_name: string;
}

const MENTION = /@\[([^\]]*)\]\(mention:\/\/user\/(\d+)\)/g;

/** The link a mention is written as. */
export function mentionLink(id: number, displayName: string): string {
  return `@[${displayName}](mention://user/${id})`;
}

/** The people a message names, in the order they were named, once each. */
export function mentionedIds(body: string): number[] {
  const seen = new Set<number>();
  for (const match of body.matchAll(MENTION)) {
    seen.add(Number(match[2]));
  }
  return [...seen];
}

/**
 * A message as it is read, its mentions spelled out.
 *
 * The name comes from the register and not from the text: what was typed is a
 * snapshot of the day it was written, and only the register knows who that id
 * is now. An account that has gone keeps the name it was written under — that
 * is the one thing left that says who was meant.
 */
export function renderMentions(body: string, people: MentionablePerson[]): string {
  const names = new Map(people.map((person) => [person.id, person.display_name]));
  return body.replace(
    MENTION,
    (_whole, written: string, id: string) => `**@${names.get(Number(id)) ?? written}**`,
  );
}

/** What an attribute may not carry raw. */
function escapeAttribute(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * A stored message, as the editor takes it in.
 *
 * Editing goes through HTML: tiptap parses that, and a mention left as
 * markdown would be read as an ordinary link — clickable, pointing at
 * `mention://`, and no longer a mention at all. The way back out is the
 * node's own markdown serializer, which writes `mentionLink` again.
 */
export function mentionsToHtml(body: string): string {
  return body.replace(
    MENTION,
    (_whole, written: string, id: string) =>
      `<span data-type="mention" data-id="${escapeAttribute(id)}" data-label="${escapeAttribute(written)}"></span>`,
  );
}
