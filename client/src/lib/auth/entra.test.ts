import { beforeEach, describe, expect, it } from "vitest";

import {
  authorizationUrl,
  claimsFromIdToken,
  emailFromIdToken,
  isAllowedEmail,
  needsRefresh,
  pkcePair,
} from "./entra";

/** An identity token as Entra writes them: three parts, the middle one readable. */
function idTokenCarrying(claims: Record<string, string>): string {
  const body = btoa(JSON.stringify(claims)).replace(/\+/g, "-").replace(/\//g, "_");
  return `header.${body}.signature`;
}

describe("the address people are sent to sign in", () => {
  beforeEach(() => {
    process.env.AZURE_AD_TENANT_ID = "a-tenant";
    process.env.AZURE_AD_CLIENT_ID = "a-client";
    process.env.AZURE_AD_REDIRECT_URI =
      "http://localhost:3007/api/auth/callback/azure-ad";
  });

  it("leads to the tenant, and names who is asking", async () => {
    const url = new URL(
      await authorizationUrl({
        state: "a-state",
        nonce: "a-nonce",
        challenge: "a-challenge",
      }),
    );

    expect(url.origin + url.pathname).toBe(
      "https://login.microsoftonline.com/a-tenant/oauth2/v2.0/authorize",
    );
    expect(url.searchParams.get("client_id")).toBe("a-client");
    expect(url.searchParams.get("response_type")).toBe("code");
  });

  /**
   * Without `offline_access` Entra hands back no renewal token, and everyone
   * would sign in afresh every hour.
   */
  it("asks for what renews the session", async () => {
    const url = new URL(
      await authorizationUrl({ state: "s", nonce: "n", challenge: "c" }),
    );

    expect(url.searchParams.get("scope")).toContain("offline_access");
    expect(url.searchParams.get("scope")).toContain("openid");
  });

  /** The state foils CSRF, the nonce foils the replay of an identity token. */
  it("carries the state, the nonce and the PKCE challenge", async () => {
    const url = new URL(
      await authorizationUrl({
        state: "a-state",
        nonce: "a-nonce",
        challenge: "a-challenge",
      }),
    );

    expect(url.searchParams.get("state")).toBe("a-state");
    expect(url.searchParams.get("nonce")).toBe("a-nonce");
    expect(url.searchParams.get("code_challenge")).toBe("a-challenge");
    expect(url.searchParams.get("code_challenge_method")).toBe("S256");
  });
});

describe("the PKCE pair", () => {
  it("derives the challenge from the secret, without ever showing it", async () => {
    const { verifier, challenge } = await pkcePair();

    expect(verifier.length).toBeGreaterThanOrEqual(43);
    expect(challenge).not.toBe(verifier);
    // Base64url: what Entra expects, with nothing to escape in a URL.
    expect(challenge).toMatch(/^[A-Za-z0-9_-]+$/);
  });

  it("draws a different one every time", async () => {
    const [one, two] = [await pkcePair(), await pkcePair()];

    expect(one.verifier).not.toBe(two.verifier);
  });
});

describe("the allowed domain", () => {
  beforeEach(() => {
    process.env.ALLOWED_EMAIL_DOMAIN = "waat.fr";
  });

  it("lets the team in", () => {
    expect(isAllowedEmail("l.chen@waat.fr")).toBe(true);
    expect(isAllowedEmail("L.Chen@WAAT.FR")).toBe(true);
  });

  it("closes on whoever comes from elsewhere", () => {
    expect(isAllowedEmail("someone@other.fr")).toBe(false);
    // The suffix trap: "waat.fr.evil.com" ends in something else entirely.
    expect(isAllowedEmail("someone@waat.fr.evil.com")).toBe(false);
    expect(isAllowedEmail("")).toBe(false);
  });
});

describe("when to renew", () => {
  const now = 1_800_000_000;

  it("renews ahead of the deadline, not after it", () => {
    // A request leaving just before expiry would arrive too late: take a lead
    // rather than let a dead token through.
    expect(needsRefresh({ expiresAt: now + 30 }, now)).toBe(true);
    expect(needsRefresh({ expiresAt: now + 600 }, now)).toBe(false);
  });

  it("renews what has already expired", () => {
    expect(needsRefresh({ expiresAt: now - 1 }, now)).toBe(true);
  });
});

describe("the address read from the identity token", () => {
  it("reads where Entra puts it", () => {
    expect(
      emailFromIdToken(idTokenCarrying({ preferred_username: "l.chen@waat.fr" })),
    ).toBe("l.chen@waat.fr");
    expect(emailFromIdToken(idTokenCarrying({ email: "l.chen@waat.fr" }))).toBe(
      "l.chen@waat.fr",
    );
  });

  it("returns null rather than guess", () => {
    expect(emailFromIdToken("not-a-token")).toBeNull();
    expect(emailFromIdToken(idTokenCarrying({ sub: "no-address" }))).toBeNull();
  });
});

describe("the claims read from the identity token", () => {
  /** Without this, the nonce could not be compared and replay would go unseen. */
  it("hands back the nonce the token carries", () => {
    expect(claimsFromIdToken(idTokenCarrying({ nonce: "n-123" }))?.nonce).toBe("n-123");
  });

  it("says nothing of a token it cannot read", () => {
    expect(claimsFromIdToken("not-a-token")).toBeNull();
  });

  it("carries no nonce when the token carries none", () => {
    expect(
      claimsFromIdToken(idTokenCarrying({ preferred_username: "a@waat.fr" }))?.nonce,
    ).toBeUndefined();
  });
});
