interface PageHeaderProps {
  titre: string;
  soustitre: string;
  /** Actions acting on the whole screen, aligned right. */
  actions?: React.ReactNode;
}

/**
 * Header shared by every view.
 *
 * Title and subtitle on the left, general actions on the right, across the full
 * width: the buttons sit in the same place from one screen to the next, even
 * when the content below is narrower.
 */
export function PageHeader({ titre, soustitre, actions }: PageHeaderProps) {
  return (
    <header className="mb-6 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold">{titre}</h1>
        <p className="text-sm text-slate-500">{soustitre}</p>
      </div>

      {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
    </header>
  );
}
