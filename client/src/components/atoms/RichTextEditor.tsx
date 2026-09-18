"use client";

import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import {
  Bold,
  Code,
  Heading2,
  Heading3,
  Italic,
  Link2,
  List,
  ListOrdered,
  Quote,
  Strikethrough,
} from "lucide-react";
import { Markdown, type MarkdownStorage } from "tiptap-markdown";

/**
 * `tiptap-markdown` grafts its output onto the editor storage without exposing
 * it to the types: we go through the type it publishes rather than writing an
 * `any`.
 */
function markdownDe(editor: Editor): string {
  const stockage = editor.storage as unknown as { markdown: MarkdownStorage };
  return stockage.markdown.getMarkdown();
}

interface RichTextEditorProps {
  value: string;
  placeholder?: string;
  onChange: (markdown: string) => void;
  /** Triggered by Cmd+Enter, to save without leaving the keyboard. */
  onSubmit?: () => void;
  /** Offers headings: a sheet has structure, a weekly note does not. */
  withHeadings?: boolean;
  /** Puts the cursor in the input area as soon as it appears. */
  autoFocus?: boolean;
  /** Minimum height of the input area, in Tailwind classes. */
  hauteur?: string;
  /**
   * Takes all the height the parent leaves, the input area scrolling on its
   * own. Requires an unbroken flex chain above.
   */
  fullHeight?: boolean;
}

/** One button of the toolbar. */
function Outil({
  editor,
  isActive,
  title,
  onClick,
  children,
}: {
  editor: Editor;
  isActive: boolean;
  title: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      aria-pressed={isActive}
      // `onMouseDown` rather than `onClick`: the button would take focus and
      // the selection would be lost before the command applied.
      onMouseDown={(event) => {
        event.preventDefault();
        onClick();
        editor.chain().focus().run();
      }}
      className={`cursor-pointer rounded p-1.5 transition-colors ${
        isActive ? "bg-slate-200 text-slate-900" : "text-slate-500 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}

/**
 * Assisted writing, producing markdown.
 *
 * One writes while seeing the result, but it is markdown that goes to the
 * database: the service sheet already stores some, updates read with the same
 * rendering, and above all nothing is HTML — so there is nothing to sanitise
 * when reading back.
 */
export function RichTextEditor({
  value,
  placeholder,
  onChange,
  onSubmit,
  withHeadings = false,
  autoFocus = false,
  hauteur = "min-h-24",
  fullHeight = false,
}: RichTextEditorProps) {
  const editor = useEditor({
    // Next renders this component on the server: letting ProseMirror settle in
    // on the first render would make the HTML diverge and cause a hydration
    // error.
    immediatelyRender: false,
    // « end » and not « start »: one writes after what is
    // already there.
    autofocus: autoFocus ? "end" : false,
    extensions: [
      StarterKit.configure({ heading: { levels: [2, 3] } }),
      Link.configure({ openOnClick: false }),
      Placeholder.configure({ placeholder: placeholder ?? "" }),
      Markdown.configure({ transformPastedText: true }),
    ],
    content: value,
    editorProps: {
      attributes: {
        class: `prose prose-sm prose-slate max-w-none ${fullHeight ? "h-full" : hauteur} px-3 py-2 focus:outline-none`,
        "aria-label": placeholder ?? "Rédaction",
      },
      handleKeyDown: (_, event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && onSubmit) {
          onSubmit();
          return true;
        }
        return false;
      },
    },
    onUpdate: ({ editor }) => onChange(markdownDe(editor)),
  });

  if (!editor) {
    return <div className="min-h-32 rounded-md border border-slate-300 bg-white" />;
  }

  return (
    <div
      className={[
        "overflow-hidden rounded-md border border-slate-300 bg-white focus-within:border-slate-500",
        fullHeight ? "flex min-h-0 flex-1 flex-col" : "",
      ].join(" ")}
    >
      <EditorContent
        editor={editor}
        // The input area scrolls on its own: the toolbar stays before the
        // eyes, even at the bottom of a long sheet.
        className={fullHeight ? "min-h-0 flex-1 overflow-y-auto" : undefined}
      />

      <div className="flex flex-wrap items-center gap-0.5 border-t border-slate-200 px-1.5 py-1">
        <Outil
          editor={editor}
          title="Gras"
          isActive={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          title="Italique"
          isActive={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          title="Barré"
          isActive={editor.isActive("strike")}
          onClick={() => editor.chain().focus().toggleStrike().run()}
        >
          <Strikethrough className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          title="Code"
          isActive={editor.isActive("code")}
          onClick={() => editor.chain().focus().toggleCode().run()}
        >
          <Code className="size-3.5" aria-hidden />
        </Outil>

        {withHeadings && (
          <>
            <span aria-hidden className="mx-1 h-4 w-px bg-slate-200" />
            <Outil
              editor={editor}
              title="Titre"
              isActive={editor.isActive("heading", { level: 2 })}
              onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            >
              <Heading2 className="size-3.5" aria-hidden />
            </Outil>
            <Outil
              editor={editor}
              title="Sous-titre"
              isActive={editor.isActive("heading", { level: 3 })}
              onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            >
              <Heading3 className="size-3.5" aria-hidden />
            </Outil>
          </>
        )}

        <span aria-hidden className="mx-1 h-4 w-px bg-slate-200" />

        <Outil
          editor={editor}
          title="Liste à puces"
          isActive={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          title="Liste numérotée"
          isActive={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          title="Citation"
          isActive={editor.isActive("blockquote")}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
        >
          <Quote className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          title="Lien"
          isActive={editor.isActive("link")}
          onClick={() => {
            if (editor.isActive("link")) {
              editor.chain().focus().unsetLink().run();
              return;
            }
            const url = window.prompt("Adresse du lien");
            if (url) editor.chain().focus().setLink({ href: url }).run();
          }}
        >
          <Link2 className="size-3.5" aria-hidden />
        </Outil>
      </div>
    </div>
  );
}
