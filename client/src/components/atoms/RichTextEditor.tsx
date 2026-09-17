"use client";

import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import {
  Bold,
  Code,
  Italic,
  Link2,
  List,
  ListOrdered,
  Quote,
  Strikethrough,
} from "lucide-react";
import { Markdown, type MarkdownStorage } from "tiptap-markdown";

/**
 * `tiptap-markdown` greffe sa sortie sur le stockage de l'editeur sans
 * l'exposer aux types : on passe par le type qu'il publie plutot que d'ecrire
 * un `any`.
 */
function markdownDe(editor: Editor): string {
  const stockage = editor.storage as unknown as { markdown: MarkdownStorage };
  return stockage.markdown.getMarkdown();
}

interface RichTextEditorProps {
  valeur: string;
  placeholder?: string;
  onChange: (markdown: string) => void;
  /** Declenche par Cmd+Entree, pour enregistrer sans lacher le clavier. */
  onSubmit?: () => void;
}

/** Un bouton de la barre d'outils. */
function Outil({
  editor,
  actif,
  titre,
  onClick,
  children,
}: {
  editor: Editor;
  actif: boolean;
  titre: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      title={titre}
      aria-label={titre}
      aria-pressed={actif}
      // `onMouseDown` plutot que `onClick` : le bouton prendrait le focus et
      // la selection serait perdue avant que la commande ne s'applique.
      onMouseDown={(event) => {
        event.preventDefault();
        onClick();
        editor.chain().focus().run();
      }}
      className={`cursor-pointer rounded p-1.5 transition-colors ${
        actif ? "bg-slate-200 text-slate-900" : "text-slate-500 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}

/**
 * Redaction assistee, qui produit du markdown.
 *
 * On ecrit en voyant le resultat, mais c'est du markdown qui part en base :
 * la fiche de service en stocke deja, les mises a jour se lisent avec le meme
 * rendu, et surtout rien n'est du HTML — il n'y a donc rien a assainir a la
 * relecture.
 */
export function RichTextEditor({
  valeur,
  placeholder,
  onChange,
  onSubmit,
}: RichTextEditorProps) {
  const editor = useEditor({
    // Next rend ce composant sur le serveur : laisser ProseMirror s'installer
    // au premier rendu ferait diverger le HTML et provoquerait une erreur
    // d'hydratation.
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({ heading: { levels: [2, 3] } }),
      Link.configure({ openOnClick: false }),
      Placeholder.configure({ placeholder: placeholder ?? "" }),
      Markdown.configure({ transformPastedText: true }),
    ],
    content: valeur,
    editorProps: {
      attributes: {
        class:
          "prose prose-sm prose-slate max-w-none min-h-24 px-3 py-2 focus:outline-none",
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
    <div className="overflow-hidden rounded-md border border-slate-300 bg-white focus-within:border-slate-500">
      <EditorContent editor={editor} />

      <div className="flex flex-wrap items-center gap-0.5 border-t border-slate-200 px-1.5 py-1">
        <Outil
          editor={editor}
          titre="Gras"
          actif={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          titre="Italique"
          actif={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          titre="Barré"
          actif={editor.isActive("strike")}
          onClick={() => editor.chain().focus().toggleStrike().run()}
        >
          <Strikethrough className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          titre="Code"
          actif={editor.isActive("code")}
          onClick={() => editor.chain().focus().toggleCode().run()}
        >
          <Code className="size-3.5" aria-hidden />
        </Outil>

        <span aria-hidden className="mx-1 h-4 w-px bg-slate-200" />

        <Outil
          editor={editor}
          titre="Liste à puces"
          actif={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          titre="Liste numérotée"
          actif={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          titre="Citation"
          actif={editor.isActive("blockquote")}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
        >
          <Quote className="size-3.5" aria-hidden />
        </Outil>
        <Outil
          editor={editor}
          titre="Lien"
          actif={editor.isActive("link")}
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
