"use client";

import type { UserResponse } from "@/lib/api/generated/model";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface TeammateSelectorProps {
  teammates: UserResponse[];
  selectedId: number | null;
  onSelect: (userId: number) => void;
}

/** Choix du collaborateur consulte. Chacun peut consulter le mois de chacun. */
export function TeammateSelector({
  teammates,
  selectedId,
  onSelect,
}: TeammateSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="teammate" className="text-muted-foreground">
        Collaborateur
      </Label>

      <Select
        value={selectedId ? String(selectedId) : ""}
        onValueChange={(value) => onSelect(Number(value))}
      >
        <SelectTrigger id="teammate" className="w-52">
          {/* Le composant affiche la valeur brute : on rend le nom a la place. */}
          <SelectValue>
            {(value: string) =>
              teammates.find((user) => String(user.id) === value)?.display_name ??
              "Collaborateur"
            }
          </SelectValue>
        </SelectTrigger>

        <SelectContent>
          {teammates.map((user) => (
            <SelectItem key={user.id} value={String(user.id)}>
              {user.display_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
