/**
 * Addresses the application used to answer on, and where they now lead.
 *
 * A screen that is renamed keeps its old address alive: everyone's bookmarks
 * point at it, and a rename nobody redirects is a rename that breaks the
 * morning of whoever kept the link.
 *
 * An address listed here is spent, and is never handed to another screen.
 * Redirecting it is only possible while it leads nowhere else — reattributing
 * it would land people on a screen they did not ask for, with no error to tell
 * them so.
 */
export type LegacyRoute = {
  /** The address that was published, and that browsers still remember. */
  source: string;
  /** Where it leads now. */
  destination: string;
};

export const LEGACY_ROUTES: LegacyRoute[] = [
  // « Activité » named the screen after what it showed; it is where time is
  // declared, and « Saisie des temps » says so. The reading of what the team
  // actually did lives elsewhere.
  { source: "/activite", destination: "/timesheet" },
];
