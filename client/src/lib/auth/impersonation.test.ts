import { beforeEach, describe, expect, it } from "vitest";

import {
  IMPERSONATION_COOKIE,
  borrowedUserIdFrom,
  borrowingCookie,
  returnedCookie,
} from "./impersonation";

const SECRET = "a development session key, as long as it needs to be";

/** The cookies a browser would send back, from what a response set. */
function jar(...written: { name: string; value: string }[]) {
  return (name: string) => written.find((cookie) => cookie.name === name)?.value;
}

describe("the borrowed account", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = SECRET;
  });

  it("opens again as the teammate it was sealed on", async () => {
    const written = await borrowingCookie(42);

    expect(await borrowedUserIdFrom(jar(written))).toBe(42);
  });

  it("is nobody when nothing was ever borrowed", async () => {
    expect(await borrowedUserIdFrom(jar())).toBeNull();
  });

  /**
   * The whole reason it is sealed rather than named in a plain cookie: a
   * page that could write « je lis comme le 7 » would be a page naming its
   * own reader.
   */
  it("refuses a cookie written by hand", async () => {
    expect(
      await borrowedUserIdFrom(jar({ name: IMPERSONATION_COOKIE, value: "7" })),
    ).toBeNull();
  });

  it("refuses one sealed under another key", async () => {
    const written = await borrowingCookie(42);
    process.env.SESSION_SECRET = "an altogether other key, just as long but other";

    expect(await borrowedUserIdFrom(jar(written))).toBeNull();
  });

  it("refuses what was touched up on the way", async () => {
    const written = await borrowingCookie(42);
    const tampered = { ...written, value: written.value.slice(0, -4) + "AAAA" };

    expect(await borrowedUserIdFrom(jar(tampered))).toBeNull();
  });

  /** Read by no script on the page, and not sent to any other site. */
  it("is sealed the way the session is", async () => {
    const written = await borrowingCookie(42);

    expect(written.httpOnly).toBe(true);
    expect(written.sameSite).toBe("lax");
    expect(written.value).not.toContain("42");
  });

  it("gives the account back by expiring on the spot", () => {
    const given = returnedCookie();

    expect(given.name).toBe(IMPERSONATION_COOKIE);
    expect(given.maxAge).toBe(0);
  });
});
