"use client";

import Mention, { type MentionNodeAttrs } from "@tiptap/extension-mention";
import type { Editor, Range } from "@tiptap/react";
import type { SuggestionProps } from "@tiptap/suggestion";

import { mentionLink, type MentionablePerson } from "@/lib/mentions";

/** How many names the menu offers at once. */
const SHORTLIST = 6;

/**
 * The « @ » menu, and how a mention leaves the editor.
 *
 * Two things are settled here and nowhere else:
 *
 * - what the node writes when the document is turned back into markdown —
 *   `@[Nom](mention://user/12)`, the one shape the server reads;
 * - the plain DOM menu the suggestion opens. A list of at most six names, no
 *   portal and no floating-UI: it is anchored on the caret, which is where
 *   one is already looking.
 */
export function mentionExtension(people: MentionablePerson[]) {
  return Mention.extend({
    addStorage() {
      return {
        markdown: {
          serialize(
            state: { write: (text: string) => void },
            node: { attrs: { id: string; label?: string | null } },
          ) {
            state.write(mentionLink(Number(node.attrs.id), node.attrs.label ?? ""));
          },
          parse: {},
        },
      };
    },
  }).configure({
    // The node renders as « @Nom » and carries the id: what is read and what
    // is meant, kept apart.
    renderText: ({ node }) => `@${node.attrs.label ?? ""}`,
    HTMLAttributes: {
      class:
        "rounded bg-sky-50 px-1 py-0.5 font-medium text-sky-800 ring-1 ring-sky-100",
    },
    suggestion: {
      // Configuring `suggestion` replaces the extension's own object whole,
      // `command` included — and without it the « @Fab » one typed stays in
      // the text beside the mention it produced.
      //
      // The range the plugin hands over stops short of what has been typed
      // since the « @ », so the caret is what closes it: at the moment one
      // picks a name, it sits right after the query, whatever the plugin
      // believes. Replacing from the « @ » to there is what takes the query
      // out.
      command: ({
        editor,
        range,
        props,
      }: {
        editor: Editor;
        range: Range;
        props: MentionNodeAttrs;
      }) => {
        const caret = editor.state.selection.from;
        editor
          .chain()
          .focus()
          .insertContentAt({ from: range.from, to: Math.max(range.to, caret) }, [
            { type: "mention", attrs: props },
            { type: "text", text: " " },
          ])
          .run();
      },
      items: ({ query }: { query: string }) =>
        people
          .filter((person) =>
            person.display_name.toLowerCase().includes(query.toLowerCase()),
          )
          .slice(0, SHORTLIST),
      render: () => {
        let menu: HTMLDivElement | null = null;
        let shortlist: MentionablePerson[] = [];
        let active = 0;
        let insert: ((person: MentionablePerson) => void) | null = null;

        function draw() {
          if (!menu) return;
          menu.innerHTML = "";
          shortlist.forEach((person, index) => {
            const row = document.createElement("button");
            row.type = "button";
            row.textContent = person.display_name;
            row.className = [
              "block w-full cursor-pointer px-3 py-1.5 text-left text-sm transition-colors",
              index === active
                ? "bg-slate-100 text-slate-900"
                : "text-slate-600 hover:bg-slate-50",
            ].join(" ");
            row.addEventListener("mousedown", (event) => {
              event.preventDefault();
              insert?.(person);
            });
            menu?.appendChild(row);
          });
        }

        function place(rect: DOMRect | null) {
          if (!menu || !rect) return;
          menu.style.left = `${rect.left}px`;
          menu.style.top = `${rect.bottom + 4}px`;
        }

        return {
          onStart: (props: SuggestionProps<MentionablePerson, MentionNodeAttrs>) => {
            shortlist = props.items;
            active = 0;
            insert = (person) =>
              props.command({
                id: String(person.id),
                label: person.display_name,
              });

            menu = document.createElement("div");
            menu.className =
              "fixed z-50 min-w-48 overflow-hidden rounded-md border border-slate-300 bg-white py-1 shadow-md";
            document.body.appendChild(menu);
            draw();
            place(props.clientRect?.() ?? null);
          },
          onUpdate: (props: SuggestionProps<MentionablePerson, MentionNodeAttrs>) => {
            shortlist = props.items;
            active = 0;
            draw();
            place(props.clientRect?.() ?? null);
          },
          onKeyDown: (props: { event: KeyboardEvent }) => {
            if (!shortlist.length) return false;
            if (props.event.key === "ArrowDown") {
              active = (active + 1) % shortlist.length;
              draw();
              return true;
            }
            if (props.event.key === "ArrowUp") {
              active = (active - 1 + shortlist.length) % shortlist.length;
              draw();
              return true;
            }
            if (props.event.key === "Enter") {
              insert?.(shortlist[active]);
              return true;
            }
            if (props.event.key === "Escape") {
              menu?.remove();
              menu = null;
              return true;
            }
            return false;
          },
          onExit: () => {
            menu?.remove();
            menu = null;
          },
        };
      },
    },
  });
}
