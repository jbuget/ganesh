import { beforeEach, describe, expect, it } from "vitest";

import { openPending, safeLanding, sealPending } from "./pending";

describe("les secrets d'une connexion en cours", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = "une clef de developpement, assez longue pour servir";
  });

  it("se rouvrent tels qu'ils ont été mis de côté", async () => {
    const pending = {
      state: "un-etat",
      nonce: "un-nonce",
      verifier: "un-secret-pkce",
      landing: "/projects",
    };

    expect(await openPending(await sealPending(pending))).toEqual(pending);
  });

  it("ne laissent rien lire au passage", async () => {
    const sealed = await sealPending({
      state: "un-etat",
      nonce: "un-nonce",
      verifier: "un-secret-pkce",
      landing: "/",
    });

    expect(sealed).not.toContain("un-secret-pkce");
    expect(sealed).not.toContain("un-etat");
  });

  it("refusent un cookie forgé", async () => {
    expect(await openPending("forge")).toBeNull();
  });
});

describe("où l'on accepte d'atterrir", () => {
  it("garde le chemin demandé", () => {
    expect(safeLanding("/projects?name=ALICE")).toBe("/projects?name=ALICE");
  });

  /**
   * Sans ce garde-fou, un lien « /api/auth/login?from=https://ailleurs » ferait
   * de notre page de connexion un tremplin vers un autre site.
   */
  it("refuse de renvoyer ailleurs que chez nous", () => {
    expect(safeLanding("https://ailleurs.example")).toBe("/");
    expect(safeLanding("//ailleurs.example")).toBe("/");
    expect(safeLanding(null)).toBe("/");
    expect(safeLanding("")).toBe("/");
  });
});
