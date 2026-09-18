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
}: TeammateSelectorProps) {
  const items: TeammateItem[] = useMemo(
    () => teammates.map((user) => ({ value: user.id, label: user.display_name })),
    [teammates],
  );

  const selection = items.find((item) => item.value === selectedId) ?? null;

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="teammate" className="text-muted-foreground">
        Collaborateur
      </Label>

      <Combobox
        items={items}
        value={selection}
        isItemEqualToValue={(item, value) => item.value === value.value}
        onValueChange={(teammate) => {
          if (teammate) onSelect((teammate as TeammateItem).value);
        }}
      >
        <ComboboxTrigger id="teammate" className="w-52">
          <ComboboxValue placeholder="Collaborateur" />
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
