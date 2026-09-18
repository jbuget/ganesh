"use client";

interface PageLayoutProps {
  /** The screen header, which does not scroll. */
  header: React.ReactNode;
  /**
   * For a screen that arranges its own scrolling — the kanban and its columns —
   * instead of leaving it to the whole page.
   */
  defilementInterne?: boolean;
  children: React.ReactNode;
}

/**
 * The skeleton shared by every view: a fixed header, content scrolling beneath.
 *
 * The screen fits the window and only the content moves: the title and the
 * actions stay before the eyes, however long the list. It is also what lets
 * table headers stick, failing which they would latch onto the window and slip
 * under the page's own header.
 */
export function PageLayout({
  header,
  defilementInterne = false,
  children,
}: PageLayoutProps) {
  return (
    <main className="flex h-screen flex-col">
      <div className="shrink-0 px-6 pt-6">{header}</div>

      <div
        className={[
          "min-h-0 flex-1 px-6 pb-6",
          defilementInterne ? "overflow-hidden" : "overflow-y-auto",
        ].join(" ")}
      >
        {children}
      </div>
    </main>
  );
}
