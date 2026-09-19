"use client";

import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";

interface SearchFieldProps {
  value: string;
  onChange: (value: string) => void;
  /**
   * What is being searched: « Rechercher un projet ».
   *
   * It labels the field and shows inside it while it is empty. The two must say
   * the same thing: a placeholder is not a label, and a field named one way to
   * the eye and another to a screen reader is two fields.
   */
  label: string;
}

/**
 * The field a list is searched from.
 *
 * Every keystroke is passed on, with no confirmation: one narrows a list by
 * typing and reads the result as it goes, rather than typing then submitting.
 *
 * The magnifier is decorative — the field already says what it is — and lets
 * the click through to the field behind it.
 */
export function SearchField({ value, onChange, label }: SearchFieldProps) {
  return (
    <div className="relative">
      <Search
        className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400"
        aria-hidden
      />
      <Input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={label}
        aria-label={label}
        className="h-9 w-64 pl-8"
      />
    </div>
  );
}
