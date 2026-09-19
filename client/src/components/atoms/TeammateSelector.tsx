"use client";

import { useMemo } from "react";

import type { UserResponse } from "@/lib/api/generated/model";
import { Label } from "@/components/ui/label";
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  ComboboxTrigger,
  ComboboxValue,
} from "@/components/ui/combobox";

interface TeammateSelectorProps {
  teammates: UserResponse[];
  selectedId: number | null;
  onSelect: (userId: number) => void;
  /** What the field asks for. « Collaborateur » on the activity screen. */
  label?: string;
  /** Ties the label to the field, and tells two selectors on one page apart. */
  id?: string;
  /**
   * Label above rather than beside.
   *
   * A toolbar reads across, a form reads down: the same control, laid out the
   * way the screen around it is.
   */
  stacked?: boolean;
}

/** An offered teammate: `value` / `label` is the shape Base UI can read. */
interface TeammateItem {
  value: number;
  label: string;
}

/**
 * Choosing which teammate is looked at. Anyone may look at anyone's month.
 *
 * The search field at the top of the menu saves scanning the whole team for a
 * name, as in the other menus of the application.
 */
export function TeammateSelector({
  teammates,
  selectedId,
  onSelect,
  label = "Collaborateur",
  id = "teammate",
  stacked = false,
}: TeammateSelectorProps) {
  const items: TeammateItem[] = useMemo(
    () => teammates.map((user) => ({ value: user.id, label: user.display_name })),
    [teammates],
  );

  const selection = items.find((item) => item.value === selectedId) ?? null;

  return (
    <div className={stacked ? "space-y-1.5" : "flex items-center gap-2"}>
      <Label htmlFor={id} className={stacked ? undefined : "text-muted-foreground"}>
        {label}
      </Label>

      <Combobox
        items={items}
        value={selection}
        isItemEqualToValue={(item, value) => item.value === value.value}
        onValueChange={(teammate) => {
          if (teammate) onSelect((teammate as TeammateItem).value);
        }}
      >
        <ComboboxTrigger id={id} className={stacked ? "w-full" : "w-52"}>
          <ComboboxValue placeholder={label} />
        </ComboboxTrigger>

        <ComboboxContent>
          <ComboboxInput placeholder="Rechercher un collaborateur…" />

          <ComboboxEmpty>Aucun collaborateur ne correspond.</ComboboxEmpty>

          <ComboboxList>
            {(teammate: TeammateItem) => (
              <ComboboxItem key={teammate.value} value={teammate}>
                {teammate.label}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    </div>
  );
}
