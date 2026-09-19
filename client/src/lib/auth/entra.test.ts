import { beforeEach, describe, expect, it } from "vitest";

import {
  authorizationUrl,
  emailFromIdToken,
  isAllowedEmail,
  needsRefresh,
  pkcePair,
} from "./entra";

/** Un jeton d'identité comme Entra les écrit : trois parties, la seconde lisible. */
function idTokenCarrying(claims: Record<string, string>): string {
  const body = btoa(JSON.stringify(claims)).replace(/\+/g, "-").replace(/\//g, "_");
  return `entete.${body}.signature`;
}

describe("l'adresse où l'on envoie se connecter", () => {
  beforeEach(() => {
    process.env.AZURE_AD_TENANT_ID = "un-tenant";
    process.env.AZURE_AD_CLIENT_ID = "un-client";
    process.env.AZURE_AD_REDIRECT_URI =
      "http://localhost:3007/api/auth/callback/azure-ad";
  });

  it("mène au tenant, et lui dit qui demande", async () => {
    const url = new URL(
      await authorizationUrl({
        state: "un-etat",
        nonce: "un-nonce",
        challenge: "un-defi",
      }),
    );

    expect(url.origin + url.pathname).toBe(
      "https://login.microsoftonline.com/un-tenant/oauth2/v2.0/authorize",
    );
    expect(url.searchParams.get("client_id")).toBe("un-client");
    expect(url.searchParams.get("response_type")).toBe("code");
  });

  /**
   * Sans `offline_access`, Entra ne rend pas de jeton de renouvellement, et il
   * faudrait se reconnecter toutes les heures.
   */
  it("demande de quoi renouveler la session", async () => {
    const url = new URL(
      await authorizationUrl({ state: "e", nonce: "n", challenge: "d" }),
    );

    expect(url.searchParams.get("scope")).toContain("offline_access");
    expect(url.searchParams.get("scope")).toContain("openid");
  });

  /** L'état déjoue le CSRF, le nonce déjoue le rejeu d'un jeton d'identité. */
  it("emporte l'état, le nonce et le défi PKCE", async () => {
    const url = new URL(
      await authorizationUrl({
        state: "un-etat",
        nonce: "un-nonce",
        challenge: "un-defi",
      }),
    );

    expect(url.searchParams.get("state")).toBe("un-etat");
    expect(url.searchParams.get("nonce")).toBe("un-nonce");
    expect(url.searchParams.get("code_challenge")).toBe("un-defi");
    expect(url.searchParams.get("code_challenge_method")).toBe("S256");
  });
});

describe("le couple PKCE", () => {
  it("dérive le défi du secret, sans jamais le montrer", async () => {
    const { verifier, challenge } = await pkcePair();

    expect(verifier.length).toBeGreaterThanOrEqual(43);
    expect(challenge).not.toBe(verifier);
    // Base64url : ce qu'attend Entra, sans caractère à échapper dans une URL.
    expect(challenge).toMatch(/^[A-Za-z0-9_-]+$/);
  });

  it("en tire un différent à chaque fois", async () => {
    const [un, deux] = [await pkcePair(), await pkcePair()];

    expect(un.verifier).not.toBe(deux.verifier);
  });
});

describe("le domaine autorisé", () => {
  beforeEach(() => {
    process.env.ALLOWED_EMAIL_DOMAIN = "waat.fr";
  });

  it("laisse entrer l'équipe", () => {
    expect(isAllowedEmail("l.chen@waat.fr")).toBe(true);
    expect(isAllowedEmail("L.Chen@WAAT.FR")).toBe(true);
  });

  it("referme sur qui vient d'ailleurs", () => {
    expect(isAllowedEmail("quelquun@autre.fr")).toBe(false);
    // Le piège du suffixe : « waat.fr.evil.com » finit par autre chose.
    expect(isAllowedEmail("quelquun@waat.fr.evil.com")).toBe(false);
    expect(isAllowedEmail("")).toBe(false);
  });
});

describe("le moment de renouveler", () => {
  const now = 1_800_000_000;

  it("renouvelle avant l'échéance, pas après", () => {
    // Une requête partie juste avant l'expiration arriverait trop tard : on
    // prend de l'avance plutôt que de laisser passer un jeton mort.
    expect(needsRefresh({ expiresAt: now + 30 }, now)).toBe(true);
    expect(needsRefresh({ expiresAt: now + 600 }, now)).toBe(false);
  });

  it("renouvelle ce qui a déjà expiré", () => {
    expect(needsRefresh({ expiresAt: now - 1 }, now)).toBe(true);
  });
});

describe("l'adresse lue dans le jeton d'identité", () => {
  it("se lit là où Entra la met", () => {
    expect(
      emailFromIdToken(idTokenCarrying({ preferred_username: "l.chen@waat.fr" })),
    ).toBe("l.chen@waat.fr");
    expect(emailFromIdToken(idTokenCarrying({ email: "l.chen@waat.fr" }))).toBe(
      "l.chen@waat.fr",
    );
  });

  it("rend null plutôt que de deviner", () => {
    expect(emailFromIdToken("pas-un-jeton")).toBeNull();
    expect(emailFromIdToken(idTokenCarrying({ sub: "sans-adresse" }))).toBeNull();
  });
});
