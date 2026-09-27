"use client";

import { ReadOnlyNotice } from "@/components/atoms/ReadOnlyNotice";
import { useIsBorrowing, useMayWrite } from "@/lib/use-may-write";

/**
 * The band a guest reads above every screen, and nobody else ever sees.
 *
 * It sits in the frame for the reason the command palette does: it belongs to
 * no screen in particular and to all of them. Said once, there, rather than on
 * each gesture — a guest meets a dozen screens, and every one of them would
 * otherwise have to explain itself.
 *
 * A borrowed account is the one case where it stands down. `useMayWrite` is
 * false there too, but the band above already says nothing may be written and
 * why — and two bands stacked, one of them addressing an audience the reader
 * is not, is how a reader learns to look past both.
 */
export function ReadOnlyBanner() {
  const mayWrite = useMayWrite();
  const isBorrowing = useIsBorrowing();

  if (mayWrite || isBorrowing) return null;
  return <ReadOnlyNotice />;
}
