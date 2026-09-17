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

/** Un collaborateur propose : `value` / `label` est la forme que Base UI sait lire. */
interface TeammateItem {
  value: number;
  label: string;
}

/**
 * Choix du collaborateur consulte. Chacun peut consulter le mois de chacun.
 *
 * Le champ de recherche en tete du menu evite de parcourir toute l'equipe pour
 * trouver un nom, comme dans les autres menus de l'application.
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
        onValueChange={(collaborateur) => {
          if (collaborateur) onSelect((collaborateur as TeammateItem).value);
        }}
      >
        <ComboboxTrigger id="teammate" className="w-52">
          <ComboboxValue placeholder="Collaborateur" />
        </ComboboxTrigger>

        <ComboboxContent>
          <ComboboxInput placeholder="Rechercher un collaborateur…" />

          <ComboboxEmpty>Aucun collaborateur ne correspond.</ComboboxEmpty>

          <ComboboxList>
            {(collaborateur: TeammateItem) => (
              <ComboboxItem key={collaborateur.value} value={collaborateur}>
                {collaborateur.label}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    </div>
  );
}
