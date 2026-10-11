"use client";

import { Bookmark } from "lucide-react";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { TagColor } from "@/lib/api/generated/model";
import { TAG_COLORS, tagMark } from "@/lib/tag-colors";

interface TagColorPickerProps {
  value: TagColor;
  /** What the trigger is called, for assistive tech: it shows a colour, no words. */
  label: string;
  onChange: (color: TagColor) => void;
}

/**
 * The colour of a tag, chosen from the palette.
 *
 * Ten colours and no more: the domain names them, and a free choice would give
 * twenty blues nobody can tell apart. Each is drawn as the bookmark the tag
 * wears, so the choice looks like what it changes.
 */
export function TagColorPicker({ value, label, onChange }: TagColorPickerProps) {
  const [isOpen, setOpen] = useState(false);

  return (
    <Popover open={isOpen} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label={label}
        className="flex cursor-pointer items-center rounded p-1.5 transition-colors hover:bg-slate-100"
      >
        <Bookmark className={`size-3.5 fill-current ${tagMark(value)}`} aria-hidden />
      </PopoverTrigger>

      <PopoverContent align="start" className="w-auto gap-0 p-1.5">
        <div className="grid grid-cols-5 gap-0.5">
          {TAG_COLORS.map((color) => (
            <button
              key={color.value}
              type="button"
              aria-label={color.label}
              title={color.label}
              aria-pressed={color.value === value}
              onClick={() => {
                onChange(color.value);
                setOpen(false);
              }}
              className="flex cursor-pointer items-center justify-center rounded p-2 transition-colors hover:bg-slate-100 aria-pressed:bg-slate-100 aria-pressed:ring-1 aria-pressed:ring-slate-400"
            >
              <Bookmark className={`size-4 fill-current ${color.mark}`} aria-hidden />
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
