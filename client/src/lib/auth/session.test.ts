import { beforeEach, describe, expect, it } from "vitest";

import { openSession, sealSession, type Session } from "./session";

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
