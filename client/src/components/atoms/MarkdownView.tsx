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
 *
 * An image written in the markdown — a capture pasted into an update, served
 * by the BFF — is bounded rather than shown at whatever size it was taken:
 * a screenshot of a whole screen would otherwise push the thread under it out
 * of sight.
 */
export function MarkdownView({ body }: MarkdownViewProps) {
  return (
    <div className="prose prose-sm prose-slate max-w-none prose-headings:font-semibold prose-a:text-sky-700 prose-code:before:content-none prose-code:after:content-none prose-img:max-h-96 prose-img:rounded prose-img:border prose-img:border-slate-300">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
    </div>
  );
}
