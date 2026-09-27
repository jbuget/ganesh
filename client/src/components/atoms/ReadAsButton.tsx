import { Eye } from "lucide-react";

interface ReadAsButtonProps {
  /** The account that would be opened, named so nobody opens the wrong one. */
  name: string;
  onClick: () => void;
  disabled: boolean;
  /** What the API said, when it refused. */
  refusal: string | null;
}

/**
 * The way into somebody else's screens, offered to an administrator.
 *
 * It says what it does *and* what it does not: an administrator who expected
 * to be able to fill a month in from inside somebody's account would find out
 * by clicking, on a refusal, three screens later.
 */
export function ReadAsButton({ name, onClick, disabled, refusal }: ReadAsButtonProps) {
  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className="inline-flex cursor-pointer items-center gap-2 rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Eye className="size-4" aria-hidden />
        Lire Ganesh comme {name}
      </button>

      <p className="text-xs text-slate-500">
        Vous verrez ses écrans sans rien pouvoir y saisir. Un bandeau le rappelle, et
        vous rend votre compte.
      </p>

      {refusal && (
        <p role="alert" className="text-xs text-red-600">
          {refusal}
        </p>
      )}
    </div>
  );
}
