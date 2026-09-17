import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownViewProps {
  texte: string;
}

/**
 * Rendu d'un texte markdown.
 *
 * `rehype-raw` n'est deliberement pas branche : le HTML ecrit dans le markdown
 * est ignore plutot qu'injecte. Une fiche se redige a plusieurs et finira
 * ailleurs qu'ici — il n'y a donc rien a assainir, puisque rien n'est execute.
 *
 * `remark-gfm` apporte ce qu'on ecrit sans y penser : tableaux, listes a
 * cocher, barre, liens bruts.
 */
export function MarkdownView({ texte }: MarkdownViewProps) {
  return (
    <div className="prose prose-sm prose-slate max-w-none prose-headings:font-semibold prose-a:text-sky-700 prose-code:before:content-none prose-code:after:content-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{texte}</ReactMarkdown>
    </div>
  );
}
