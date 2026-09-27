/**
 * Where the BFF relays to: the API, and the prefix it answers under.
 *
 * One address, read in one place. The relay is not the only handler that
 * calls the API — starting a borrowing asks it first whether it would be
 * allowed — and two readings of `API_PREFIX` are two chances of one of them
 * falling back to something else.
 */
const API_URL = process.env.API_URL ?? "http://localhost:8000";

// `||` rather than `??`: an API_PREFIX left empty in the environment is a
// variable nobody filled in, not a deliberate empty prefix — and `??` would
// take it for one, relaying to an address without /api/v1.
const API_PREFIX = process.env.API_PREFIX || "/api/v1";

/** The API's address for a path the browser asked for, prefix included. */
export function upstream(path: string): string {
  return `${API_URL}${API_PREFIX}${path}`;
}
