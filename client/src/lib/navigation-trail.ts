"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

/**
 * The screens crossed since the page was loaded.
 *
 * A sheet is reached from a dozen places — a panel on any screen, the palette,
 * a notification, the project a package belongs to — and the way out has to
 * lead back to the one it was opened from. The browser already holds that,
 * with the state of the screen in the bargain: the filters set and the panel
 * open live in the address. All that is missing is knowing whether there is a
 * step of ours to walk back at all, since a link shared in a message opens a
 * sheet with nothing behind it.
 *
 * Module state, therefore reset by a load — which is exactly the question
 * asked: was this screen reached from another one *in this tab's visit*.
 */
let currentScreen: string | null = null;
let cameFromAnother = false;

const subscribers = new Set<() => void>();

function subscribe(callback: () => void) {
  subscribers.add(callback);
  return () => {
    subscribers.delete(callback);
  };
}

/** Records the screen one has just landed on. */
function recordScreen(screen: string): void {
  // The address is written to without moving — a filter, a panel opening — and
  // the screen is recorded again. Nothing was left.
  if (screen === currentScreen) return;

  cameFromAnother = currentScreen !== null;
  currentScreen = screen;
  // A screen renders before the arrival at it is recorded: without a word to
  // those reading the trail, a sheet would keep the answer meant for the
  // screen one has just left.
  subscribers.forEach((callback) => callback());
}

/** Whether the screen one is standing on was reached from another of ours. */
function arrivedFromAnotherScreen(): boolean {
  return cameFromAnother;
}

/** Server-side nothing has been crossed: the trail belongs to a browser. */
function onServer(): boolean {
  return false;
}

/**
 * Starts afresh, as a load does in a browser — which is what the tests need,
 * jsdom loading nothing. The trail is written and read by the two hooks below,
 * and by nothing else.
 */
export function forgetTrail(): void {
  currentScreen = null;
  cameFromAnother = false;
}

/**
 * Follows the screens, from the frame that holds them all.
 *
 * Called by the sidebar, which is mounted once above every screen and never
 * unmounted: it therefore records the arrival before the screen itself reads
 * it, which a screen doing its own recording could not guarantee.
 */
export function useNavigationTrail(): void {
  const pathname = usePathname();

  useEffect(() => {
    if (pathname) recordScreen(pathname);
  }, [pathname]);
}

/** Where a screen goes back to when nothing was left behind. */
export interface Fallback {
  href: string;
  label: string;
}

/**
 * The way out of a screen: an address one can name, or a step to walk back,
 * which no address describes.
 *
 * The two are not drawn alike. An address is a link — it opens in a new tab,
 * and says where it leads. A step back is a gesture, and a button.
 */
export type WayBack =
  | { label: string; href: string; back?: undefined }
  | { label: string; href?: undefined; back: () => void };

/**
 * The way out of a screen one goes into rather than to.
 *
 * Going back to where one came from cannot be named — hence « Retour ». With
 * nothing behind, the fallback is named instead: a control that says where it
 * leads is worth more than one that says « back » and does not go back.
 *
 * The trail is read as the external state it is: it is written by an effect,
 * after this screen has already rendered once.
 */
export function useWayBack(fallback: Fallback): WayBack {
  const router = useRouter();
  const fromAnother = useSyncExternalStore(
    subscribe,
    arrivedFromAnotherScreen,
    onServer,
  );

  // The fallback is an address: it is handed back as it stands, to be drawn as
  // the link it is.
  if (!fromAnother) return fallback;

  return { label: "Retour", back: () => router.back() };
}
