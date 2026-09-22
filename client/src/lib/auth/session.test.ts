import { beforeEach, describe, expect, it } from "vitest";

import {
  SESSION_COOKIE,
  clearedSessionCookies,
  openSession,
  sealSession,
  sealedSessionFrom,
  sessionCookies,
  type Session,
} from "./session";

const SECRET = "a development session key, as long as it needs to be";

const session: Session = {
  idToken: "eyJ.a.token",
  refreshToken: "a-renewal-token",
  expiresAt: 1_800_000_000,
  email: "l.chen@waat.fr",
};

describe("the sealed session", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = SECRET;
  });

  it("opens again just as it was sealed", async () => {
    const sealed = await sealSession(session);

    expect(await openSession(sealed)).toEqual(session);
  });

  /**
   * The cookie goes to the reader: what it carries must be readable here
   * alone. A token in the clear would be readable by whoever intercepts it.
   */
  it("lets nothing be read of what it carries", async () => {
    const sealed = await sealSession(session);

    expect(sealed).not.toContain("eyJ.a.token");
    expect(sealed).not.toContain("a-renewal-token");
    expect(sealed).not.toContain("l.chen@waat.fr");
  });

  it("refuses a session another key sealed", async () => {
    const sealed = await sealSession(session);
    process.env.SESSION_SECRET = "an altogether other key, just as long but other";

    expect(await openSession(sealed)).toBeNull();
  });

  it("refuses what was touched up on the way", async () => {
    const sealed = await sealSession(session);
    const tampered = sealed.slice(0, -4) + "AAAA";

    expect(await openSession(tampered)).toBeNull();
  });

  /** The fallback door issues none: a session without a renewal token is
   *  still a valid session. */
  it("accepts a session with nothing to renew it with", async () => {
    const local = { ...session, refreshToken: "" };

    expect(await openSession(await sealSession(local))).toEqual(local);
  });

  it("returns null on a cookie that means nothing", async () => {
    expect(await openSession("anything at all")).toBeNull();
    expect(await openSession("")).toBeNull();
  });
});

/*
  A browser drops a cookie over 4 096 bytes without a word — no error, no
  console, nothing but a session that was never there on the next request. A
  sealed session sits right on that line: an identity token and the one that
  renews it, encrypted together, weigh between three and eight kilobytes
  depending on whose claims they carry.

  That is how it showed: the day production moved to Entra, half the team
  signed in and the other half came back to the sign-in page with nothing to
  say why. The measure settled it — 3 799 bytes for a session that worked, on
  a limit of 4 096.
*/
describe("a session too big for one cookie", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = SECRET;
  });

  /** The store a browser would present, from the cookies it was handed. */
  function browser(cookies: { name: string; value: string }[]) {
    return (name: string) => cookies.find((cookie) => cookie.name === name)?.value;
  }

  const heavy: Session = { ...session, idToken: "e".repeat(6_000) };

  it("is written across several cookies, none of them near the limit", async () => {
    const written = sessionCookies(await sealSession(heavy));

    expect(written.length).toBeGreaterThan(1);
    for (const cookie of written) {
      expect(cookie.name.length + cookie.value.length).toBeLessThan(4_096);
    }
  });

  it("opens again from the cookies it was cut into", async () => {
    const written = sessionCookies(await sealSession(heavy));

    const sealed = sealedSessionFrom(browser(written));

    expect(await openSession(sealed ?? "")).toEqual(heavy);
  });

  it("still opens a session written before the cut", async () => {
    // A fortnight of live sessions were written as one cookie. Signing
    // everybody out to ship this would be a fix nobody asked for.
    const sealed = await sealSession(session);

    const read = sealedSessionFrom(browser([{ name: SESSION_COOKIE, value: sealed }]));

    expect(await openSession(read ?? "")).toEqual(session);
  });

  it("takes away the cookies the previous session used and this one does not", async () => {
    // Left behind, a piece of the old session is read glued to the new one,
    // and nothing opens at all.
    const written = sessionCookies(await sealSession(session), [
      `${SESSION_COOKIE}.0`,
      `${SESSION_COOKIE}.1`,
      `${SESSION_COOKIE}.2`,
    ]);

    const emptied = written.filter((cookie) => cookie.value === "");
    expect(emptied.map((cookie) => cookie.name)).toEqual([
      `${SESSION_COOKIE}.1`,
      `${SESSION_COOKIE}.2`,
    ]);
    expect(emptied.every((cookie) => cookie.maxAge === 0)).toBe(true);
  });

  it("names every cookie a session is written across when signing out", () => {
    const cleared = clearedSessionCookies([
      SESSION_COOKIE,
      `${SESSION_COOKIE}.0`,
      `${SESSION_COOKIE}.1`,
      "some_other_cookie",
    ]);

    expect(cleared.map((cookie) => cookie.name)).toEqual([
      SESSION_COOKIE,
      `${SESSION_COOKIE}.0`,
      `${SESSION_COOKIE}.1`,
    ]);
    expect(cleared.every((cookie) => cookie.maxAge === 0)).toBe(true);
  });
});
