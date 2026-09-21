/**
 * What an editor should take out of a paste or a drop.
 *
 * Reading a `DataTransfer` is the one part of the gesture worth testing on
 * its own: the rest is ProseMirror inserting a node at a cursor.
 *
 * Only what arrives as a *file* counts. An image copied from a web page comes
 * as HTML pointing at somebody else's address, and following that would put a
 * link to a server we do not hold into a thread meant to outlive it — tiptap
 * is left to deal with that as it already does.
 */

/** The images in what was pasted or dropped, in the order they came. */
export function imagesIn(data: DataTransfer | null): File[] {
  if (!data) return [];
  return Array.from(data.files).filter((file) => file.type.startsWith("image/"));
}
