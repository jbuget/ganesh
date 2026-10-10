import ReactMarkdown, { type Options } from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownViewProps {
  body: string;
  /** How a link is drawn, when a screen has more to say than « a link ». */
  renderLink?: (href: string, children: React.ReactNode) => React.ReactNode;
  /** Remark plugins run after the ones every markdown here gets. */
  plugins?: Options["remarkPlugins"];
  /**
   * Whether an image is drawn. A text written by a model is not: an image
   * fetches its address the moment it is drawn, and an address a model was
   * talked into writing can carry whatever it read out of Ganesh.
   */
  images?: boolean;
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
export function MarkdownView({
  body,
  renderLink,
  plugins = [],
  images = true,
}: MarkdownViewProps) {
  return (
    <div className="prose prose-sm prose-slate max-w-none prose-headings:font-semibold prose-a:text-sky-700 prose-code:before:content-none prose-code:after:content-none prose-img:max-h-96 prose-img:rounded prose-img:border prose-img:border-slate-300">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, ...(plugins ?? [])]}
        disallowedElements={images ? undefined : ["img"]}
        components={
          renderLink
            ? { a: ({ href, children }) => renderLink(href ?? "", children) }
            : undefined
        }
      >
        {body}
      </ReactMarkdown>
    </div>
  );
}
