import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  appOrigin,
  landingUrl,
  openPending,
  safeLanding,
  sealPending,
} from "./pending";

describe("the secrets of a sign-in under way", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = "a development key, long enough to serve";
  });

  it("open again just as they were set aside", async () => {
    const pending = {
      state: "a-state",
      nonce: "a-nonce",
      verifier: "a-pkce-secret",
      landing: "/projects",
    };

    expect(await openPending(await sealPending(pending))).toEqual(pending);
  });

  it("let nothing be read on the way", async () => {
    const sealed = await sealPending({
      state: "a-state",
      nonce: "a-nonce",
      verifier: "a-pkce-secret",
      landing: "/",
    });

    expect(sealed).not.toContain("a-pkce-secret");
    expect(sealed).not.toContain("a-state");
  });

  it("refuse a forged cookie", async () => {
    expect(await openPending("forged")).toBeNull();
  });
});

describe("where one is allowed to land", () => {
  it("keeps the path that was asked for", () => {
    expect(safeLanding("/projects?name=ALICE")).toBe("/projects?name=ALICE");
  });

  /**
   * Without this guard, a link "/api/auth/login?from=https://elsewhere" would
   * turn our sign-in page into a springboard to another site.
   */
  it("refuses to send anywhere but home", () => {
    expect(safeLanding("https://elsewhere.example")).toBe("/");
    expect(safeLanding("//elsewhere.example")).toBe("/");
    expect(safeLanding(null)).toBe("/");
    expect(safeLanding("")).toBe("/");
  });

  /**
   * A backslash counts for a slash in the URL parser: without this,
   * "/\elsewhere.example" redirects off the site as surely as
   * "//elsewhere.example", and the sign-in page becomes a springboard.
   */
  it("refuses paths opening on a backslash too", () => {
    expect(safeLanding("/\\elsewhere.example")).toBe("/");
    expect(safeLanding("/\\\\elsewhere.example")).toBe("/");
    expect(safeLanding("/\\/elsewhere.example")).toBe("/");
  });

  it("keeps a path carrying a backslash further along", () => {
    expect(safeLanding("/projects?name=a%5Cb")).toBe("/projects?name=a%5Cb");
  });
});

describe("the final address", () => {
  const origin = "https://ganesh.waat.tools";

  it("resolves a path of ours", () => {
    expect(landingUrl("/projects?name=ALICE", origin).toString()).toBe(
      `${origin}/projects?name=ALICE`,
    );
  });

  /** The second lock: whatever the parser makes of the path, the address it
   *  comes out with must be ours. */
  it("brings everything resolving elsewhere back home", () => {
    expect(landingUrl("/\\elsewhere.example", origin).toString()).toBe(`${origin}/`);
    expect(landingUrl("https://elsewhere.example/x", origin).toString()).toBe(
      `${origin}/`,
    );
    expect(landingUrl("", origin).toString()).toBe(`${origin}/`);
  });
});

describe("the origin the application answers from", () => {
  const initial = { ...process.env };
  afterEach(() => {
    process.env = { ...initial };
  });

  /**
   * Behind CloudFront the compute server knows itself as localhost:3000, and a
   * redirect built from the request sent people to an address that is not the
   * site. What the environment says the application answers from is the only
   * thing that survives the hops.
   */
  it("prefers what the environment declares over what the request believes", () => {
    process.env.APP_URL = "https://ganesh.waat.tools";

    expect(appOrigin("https://localhost:3000")).toBe("https://ganesh.waat.tools");
  });

  it("keeps the origin alone, whatever path APP_URL carries", () => {
    process.env.APP_URL = "https://ganesh.waat.tools/quelque-part";

    expect(appOrigin("https://localhost:3000")).toBe("https://ganesh.waat.tools");
  });

  it("falls back on the request when nothing is declared", () => {
    delete process.env.APP_URL;

    expect(appOrigin("http://localhost:3005")).toBe("http://localhost:3005");
  });

  /** An unusable APP_URL must not take the sign-in down with it. */
  it("falls back on the request when what is declared makes no sense", () => {
    process.env.APP_URL = "pas-une-adresse";

    expect(appOrigin("http://localhost:3005")).toBe("http://localhost:3005");
  });
});
