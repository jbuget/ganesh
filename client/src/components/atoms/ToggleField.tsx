"use client";

interface ToggleFieldProps {
  value: boolean;
  label: string;
  /** Said when the switch is on, and when it is off: a state, not a command. */
  onText: string;
  offText: string;
  /** Why the switch cannot be turned on, if anything stands in the way. */
  blockedBy?: string | null;
  onChange: (value: boolean) => void | Promise<void>;
}

/**
 * A yes or no that reads as a sentence.
 *
 * The sheet never shows a bare checkbox: a row says what is true of the
 * mission, so the switch carries the words rather than a tick the reader has to
 * interpret.
 */
export function ToggleField({
  value,
  label,
  onText,
  offText,
  blockedBy,
  onChange,
}: ToggleFieldProps) {
  const blocked = !value && Boolean(blockedBy);

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <button
        type="button"
        role="switch"
        aria-checked={value}
        aria-label={label}
        disabled={blocked}
        onClick={() => void onChange(!value)}
        className="flex cursor-pointer items-center gap-2 text-sm disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span
          className={`relative h-4 w-7 shrink-0 rounded-full transition-colors ${
            value ? "bg-emerald-500" : "bg-slate-300"
          }`}
          aria-hidden
        >
          <span
            className={`absolute top-0.5 size-3 rounded-full bg-white transition-all ${
              value ? "left-3.5" : "left-0.5"
            }`}
          />
        </span>
        <span className={value ? "text-slate-700" : "text-slate-400"}>
          {value ? onText : offText}
        </span>
      </button>

      {blocked && <span className="text-xs text-amber-600">{blockedBy}</span>}
    </div>
  );
}
