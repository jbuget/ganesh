/**
 * One piece of work at a time, for a given key.
 *
 * A page load fires several requests at once, and each one passing through
 * the relay finds the same session about to expire. Without this they would
 * all go and renew it, spending the same renewal token as many times over —
 * and the last cookie written would be the one that counts, the others lost.
 *
 * Whoever asks while a renewal is already running waits for that one instead
 * of starting another.
 */
const running = new Map<string, Promise<unknown>>();

export function once<T>(key: string, start: () => Promise<T>): Promise<T> {
  const inFlight = running.get(key) as Promise<T> | undefined;
  if (inFlight) return inFlight;

  // Cleared whichever way it ends: a failure must not keep the next attempt
  // waiting on a promise that will never settle again.
  const started = start().finally(() => {
    running.delete(key);
  });
  running.set(key, started);
  return started;
}
