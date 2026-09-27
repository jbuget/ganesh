"use client";

import { useState } from "react";

import { ReadAsButton } from "@/components/atoms/ReadAsButton";
import { SheetSectionTitle } from "@/components/atoms/SheetSectionTitle";
import type { UserResponse } from "@/lib/api/generated/model";
import { useCurrentUser } from "@/lib/api/queries";
import { useReadAs } from "@/lib/use-read-as";

interface ReadAsAccountProps {
  user: UserResponse;
}

/**
 * « Lire comme » — the gesture, and everything that decides whether it shows.
 *
 * Self-contained rather than threaded down as props from the team list: the
 * three conditions are the API's own, and a panel passing them along would be
 * a second place for them to drift. What shows here is exactly what
 * `read_as` would accept.
 *
 * It shows for an administrator, on somebody else's account, and only while
 * that account is open: behind a closed door there is no screen to go and
 * look at, and a borrowed administrator is already reading as somebody.
 */
export function ReadAsAccount({ user }: ReadAsAccountProps) {
  const { user: me } = useCurrentUser();
  const { readAs, isMoving, isBorrowing } = useReadAs();
  const [refusal, setRefusal] = useState<string | null>(null);

  const mayReadAsThem =
    me?.role === "ADMIN" && !isBorrowing && me.id !== user.id && user.is_active;
  if (!mayReadAsThem) return null;

  return (
    <section className="mt-6 space-y-2">
      <SheetSectionTitle>Lire comme</SheetSectionTitle>
      <ReadAsButton
        name={user.display_name}
        disabled={isMoving}
        refusal={refusal}
        onClick={async () => setRefusal(await readAs(user.id))}
      />
    </section>
  );
}
