import Link from "next/link";

interface NameLinkProps {
  href: string;
  children: React.ReactNode;
}

/**
 * A link in an assistant's answer, drawn after what it leads to.
 *
 * The names are what a reader scans an answer for: a project reads in the
 * blue of a link to its sheet, a person in strong type leading to their
 * panel. Anything else is drawn as words, never as a link.
 */
export function NameLink({ href, children }: NameLinkProps) {
  if (href.startsWith("/projects/")) {
    return (
      <Link
        href={href}
        className="cursor-pointer font-medium text-sky-700 no-underline hover:underline"
      >
        {children}
      </Link>
    );
  }
  if (href.startsWith("/users")) {
    // Important on purpose: the prose around it colours every link blue, and
    // a person read in the blue of a project would be read as one.
    return (
      <Link
        href={href}
        className="cursor-pointer font-semibold text-slate-900! no-underline decoration-slate-400 underline-offset-2 hover:underline"
      >
        {children}
      </Link>
    );
  }
  // Anything else stays words. An answer is written by a model that read
  // what others typed, and a link it was talked into writing is a link
  // somebody would follow on its word.
  return <span>{children}</span>;
}
