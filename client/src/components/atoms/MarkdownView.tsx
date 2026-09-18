import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownViewProps {
  body: string;
}

/**
 * Rendering markdown text.
 *
 * `rehype-raw` is deliberately not wired in: HTML written in the markdown is
 * ignored rather than injected. A sheet is written by several people and will
 * end up elsewhere than here — so there is nothing to sanitise, since nothing
 * is executed.
 *
 * `remark-gfm` brings what people write without thinking: tables, checklists,
 * strikethrough, bare links.
 */
export function MarkdownView({ body }: MarkdownViewProps) {
  return (
    <div className="prose prose-sm prose-slate max-w-none prose-headings:font-semibold prose-a:text-sky-700 prose-code:before:content-none prose-code:after:content-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
    </div>
  );
}
