"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

interface InlineTextAreaProps {
  value: string | null | undefined;
  /** What the row asks for, shown as the empty state and read by assistive tech. */
  label: string;
  placeholder?: string;
  /** Whether the reader may write. */
  editable?: boolean;
  onChange: (value: string | null) => void | Promise<void>;
}

/**
 * Several lines of text that edit where they show.
 *
 * The same reading as `InlineTextField`, for what does not fit on one line: a
 * problem somebody is describing runs to a paragraph, and a single-line box
 * would quietly tell them to keep it short. Enter therefore makes a new line,
 * and what closes the field is leaving it.
 */
export function InlineTextArea({
  value,
  label,
  placeholder,
  editable = true,
  onChange,
}: InlineTextAreaProps) {
  const [entry, setEntry] = useState<string | null>(null);
  const [refusal, setRefusal] = useState<string | null>(null);

  function commit() {
    if (entry === null) return;
    const trimmed = entry.trim();
    const next = trimmed === "" ? null : trimmed;
    if (next === (value ?? null)) {
      setEntry(null);
      setRefusal(null);
      return;
    }
    void (async () => {
      try {
        await onChange(next);
        setEntry(null);
        setRefusal(null);
      } catch {
        setRefusal("Enregistrement impossible.");
      }
    })();
  }

  if (!editable) {
    return value ? (
      <p className="whitespace-pre-wrap text-sm text-slate-700">{value}</p>
    ) : (
      <span className="text-sm text-slate-400">Non renseigné</span>
    );
  }

  if (entry !== null) {
    return (
      <div className="space-y-1">
        <textarea
          autoFocus
          rows={4}
          value={entry}
          aria-label={label}
          placeholder={placeholder}
          onChange={(event) => {
            setEntry(event.target.value);
            setRefusal(null);
          }}
          onBlur={commit}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              // Cancelling a field cancels the field, not the visit: without
              // this the panel behind would close on the same key.
              event.stopPropagation();
              setEntry(null);
              setRefusal(null);
            }
          }}
          className={`w-full rounded border px-1.5 py-1 text-sm focus:outline-none ${
            refusal ? "border-red-400" : "border-slate-400"
          }`}
        />
        {refusal && <p className="text-xs text-red-600">{refusal}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <button
        type="button"
        aria-label={label}
        onClick={() => setEntry(value ?? "")}
        className="-mx-1 block w-full cursor-pointer rounded px-1 py-0.5 text-left text-sm transition-colors hover:bg-slate-100"
      >
        {value ? (
          <span className="block whitespace-pre-wrap text-slate-700">{value}</span>
        ) : (
          <span className="flex items-center gap-1 text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            {placeholder ?? label}
          </span>
        )}
      </button>

      {refusal && <p className="text-xs text-red-600">{refusal}</p>}
    </div>
  );
}
