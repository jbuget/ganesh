import { Eye, LogOut } from "lucide-react";

interface ImpersonationNoticeProps {
  /** The account being read. */
  readerName: string;
  /** Whoever is reading it, named so the band says whose screen is whose. */
  borrowerName: string;
  onLeave: () => void;
  /** True while the account is being given back. */
  isLeaving: boolean;
}

/**
 * The band an administrator reads while looking at Ganesh as somebody else.
 *
 * It sticks to the top of the screen and never scrolls away, which is the one
 * thing it must do: what it says stops being true the moment one forgets it,
 * and the way out has to be wherever the reader happens to be.
 *
 * It names the account being read rather than only saying « emprunt en
 * cours ». Two teammates' screens look alike; a name is what tells the reader
 * they opened the one they meant to.
 *
 * Its colour is not the read-only band's. That one is a state of an account,
 * read once and then forgotten about; this one is a state of the *reader*,
 * and reading three screens deep without noticing it is exactly the mistake
 * it exists to prevent.
 */
export function ImpersonationNotice({
  readerName,
  borrowerName,
  onLeave,
  isLeaving,
}: ImpersonationNoticeProps) {
  return (
    <div
      role="status"
      className="sticky top-0 z-50 flex flex-wrap items-center gap-x-2 gap-y-1 border-b border-violet-300 bg-violet-100 px-4 py-2 text-sm text-violet-950"
    >
      <Eye className="size-4 shrink-0" aria-hidden />
      <span>
        Vous lisez Ganesh comme <strong className="font-semibold">{readerName}</strong>.
        Aucune saisie n&apos;est possible ; {borrowerName}, c&apos;est vous.
      </span>
      <button
        type="button"
        onClick={onLeave}
        disabled={isLeaving}
        className="ml-auto inline-flex cursor-pointer items-center gap-1.5 rounded border border-violet-400 bg-white px-2 py-1 font-medium text-violet-900 transition-colors hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <LogOut className="size-3.5" aria-hidden />
        {isLeaving ? "Retour…" : "Quitter ce compte"}
      </button>
    </div>
  );
}
