"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppSidebar } from "@/components/organisms/AppSidebar";
import { CommandPalette } from "@/components/organisms/CommandPalette";
import { MoodReminder } from "@/components/organisms/MoodReminder";
import { ReadOnlyBanner } from "@/components/organisms/ReadOnlyBanner";
import { useCurrentUser } from "@/lib/api/queries";

/** The one screen a guest reaches. */
const REQUESTS = "/requests";

/**
 * The frame a screen is read in, which is not the same for everybody.
 *
 * The whole company signs in through the same Entra tenant, and whoever only
 * ever comes to express a need gets « Mes demandes » and nothing else: no
 * sidebar, no palette, no way through to the team's month, its board or its
 * plan. The API says the same thing on its side — every other route turns
 * them away — and this is what keeps the screen from offering what the server
 * would refuse.
 *
 * Nothing is drawn until we know who is there: a sidebar shown for a moment
 * and taken back would be a list of doors somebody was never meant to see.
 */
export function AppFrame({ children }: Readonly<{ children: React.ReactNode }>) {
  const { user, isLoading } = useCurrentUser();
  const pathname = usePathname();
  const router = useRouter();
  const isGuest = user?.role === "GUEST";
  const astray = isGuest && pathname !== REQUESTS;

  useEffect(() => {
    // `replace` rather than `push`: the address they typed is not a place to
    // go back to.
    if (astray) router.replace(REQUESTS);
  }, [astray, router]);

  if (isLoading || !user) return null;

  if (isGuest) {
    return <div className="min-h-screen">{astray ? null : children}</div>;
  }

  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      <div className="min-w-0 flex-1">
        {/* Whoever may not write reads the band once, here, rather than a
            dozen times over — and never a guest, who never comes this far. */}
        <ReadOnlyBanner />
        {children}
      </div>
      {/* In the frame rather than on a screen: it is reached from every one of
          them, and its shortcut listens to the whole window. */}
      <CommandPalette />
      {/* In the frame for the opposite reason: it is not reached at all. It
          comes to whoever is there at the end of the afternoon, whatever they
          happen to be reading — which is what spares « Moral de l'équipe »
          from having to ask the question itself. */}
      <MoodReminder />
    </div>
  );
}
