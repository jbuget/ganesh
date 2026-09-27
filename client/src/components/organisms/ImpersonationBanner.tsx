"use client";

import { ImpersonationNotice } from "@/components/atoms/ImpersonationNotice";
import { useCurrentUser } from "@/lib/api/queries";
import { useReadAs } from "@/lib/use-read-as";

/**
 * The band, wherever the borrowed account is being read.
 *
 * It sits in the frame for the reason the read-only band does: it belongs to
 * no screen in particular and to every one of them. And it is drawn on both
 * sides of the frame — the team's screens and the guest's one — because
 * seeing what a guest reaches is half of what borrowing an account is for.
 */
export function ImpersonationBanner() {
  const { user } = useCurrentUser();
  const { borrower, isMoving, giveBack } = useReadAs();

  if (!user || !borrower) return null;

  return (
    <ImpersonationNotice
      readerName={user.display_name}
      borrowerName={borrower.display_name}
      onLeave={giveBack}
      isLeaving={isMoving}
    />
  );
}
