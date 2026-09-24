"use client";

import { ReadOnlyNotice } from "@/components/atoms/ReadOnlyNotice";
import { useMayWrite } from "@/lib/use-may-write";

/**
 * The band a guest reads above every screen, and nobody else ever sees.
 *
 * It sits in the frame for the reason the command palette does: it belongs to
 * no screen in particular and to all of them. Said once, there, rather than on
 * each gesture — a guest meets a dozen screens, and every one of them would
 * otherwise have to explain itself.
 */
export function ReadOnlyBanner() {
  return useMayWrite() ? null : <ReadOnlyNotice />;
}
