/**
 * Waiting for a digest the server may have finished after the request gave up.
 *
 * A generation crosses the host in front of the API, which cuts a request off
 * after thirty seconds. The API goes on and writes the version all the same,
 * so an error on the screen does not mean nothing was written — it may mean
 * only that the answer never got back. Before saying it failed, ask the
 * server whether a version appeared.
 */

/**
 * How many times to look, and how long to wait between two looks.
 *
 * Two minutes in all: a generation takes some forty seconds, and the host cuts
 * the request at thirty, so the answer is still to come when the waiting
 * begins. Generous on purpose — a month with more to read takes longer, and
 * giving up early would put back the error this exists to remove.
 */
export const POLLS = 24;
export const POLL_DELAY_MS = 5000;

interface Waiting {
  /** The highest version the screen knew before asking. Zero when none. */
  before: number;
  /** Reads the highest version the server holds for the month now. */
  readLatest: () => Promise<number>;
  wait?: (ms: number) => Promise<void>;
  polls?: number;
  delayMs?: number;
}

/** The version that appeared, or nothing if none did in time. */
export async function awaitNewVersion({
  before,
  readLatest,
  wait = (ms) => new Promise((done) => setTimeout(done, ms)),
  polls = POLLS,
  delayMs = POLL_DELAY_MS,
}: Waiting): Promise<number | null> {
  for (let attempt = 0; attempt < polls; attempt += 1) {
    await wait(delayMs);
    try {
      const latest = await readLatest();
      if (latest > before) return latest;
    } catch {
      // A look that fails is one look lost, not a reason to stop looking.
    }
  }
  return null;
}
