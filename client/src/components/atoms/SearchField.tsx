"use client";

import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { SEARCH_FIELD, SEARCH_ICON } from "@/lib/search-field";

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
 * How it is drawn is written in `lib/search-field.ts`, with the field a long
 * criterion carries in its own panel: the two do the same job and must not be
 * able to drift apart.
 */
export function SearchField({ value, onChange, label }: SearchFieldProps) {
  return (
    <div className="relative">
      <Search className={SEARCH_ICON} aria-hidden />
      <Input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={label}
        aria-label={label}
        className={`w-64 ${SEARCH_FIELD}`}
      />
    </div>
  );
}
