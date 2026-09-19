import { beforeEach, describe, expect, it } from "vitest";

import { openSession, sealSession, type Session } from "./session";

const SECRET = "une clef de session de developpement, longue comme il faut";

const session: Session = {
  idToken: "eyJ.un.jeton",
  refreshToken: "un-jeton-de-renouvellement",
  expiresAt: 1_800_000_000,
  email: "l.chen@waat.fr",
};

describe("la session scellée", () => {
  beforeEach(() => {
    process.env.SESSION_SECRET = SECRET;
  });

  it("se rouvre telle qu'elle a été scellée", async () => {
    const sealed = await sealSession(session);

    expect(await openSession(sealed)).toEqual(session);
  });

  /**
   * Le cookie part chez le lecteur : ce qu'il porte ne doit se lire qu'ici.
   * Un jeton en clair dans le cookie serait lisible par qui l'intercepte.
   */
  it("ne laisse rien lire de ce qu'elle porte", async () => {
    const sealed = await sealSession(session);

    expect(sealed).not.toContain("eyJ.un.jeton");
    expect(sealed).not.toContain("un-jeton-de-renouvellement");
    expect(sealed).not.toContain("l.chen@waat.fr");
  });

  it("refuse une session qu'une autre clef a scellée", async () => {
    const sealed = await sealSession(session);
    process.env.SESSION_SECRET = "une tout autre clef, tout aussi longue mais autre";

    expect(await openSession(sealed)).toBeNull();
  });

  it("refuse ce qui a été retouché en chemin", async () => {
    const sealed = await sealSession(session);
    const tampered = sealed.slice(0, -4) + "AAAA";

    expect(await openSession(tampered)).toBeNull();
  });

  /** La porte de secours n'en délivre pas : une session sans jeton de
   *  renouvellement reste une session valable. */
  it("accepte une session sans de quoi la renouveler", async () => {
    const local = { ...session, refreshToken: "" };

    expect(await openSession(await sealSession(local))).toEqual(local);
  });

  it("rend null sur un cookie qui ne veut rien dire", async () => {
    expect(await openSession("n'importe quoi")).toBeNull();
    expect(await openSession("")).toBeNull();
  });
});
