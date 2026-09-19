import { afterEach, describe, expect, it } from "vitest";

import { isAuthDisabled, isOpenPath } from "./guard";

describe("les adresses ouvertes", () => {
  it("laisse atteindre l'écran de connexion et ce qu'il faut pour se connecter", () => {
    expect(isOpenPath("/connexion")).toBe(true);
    expect(isOpenPath("/api/auth/login")).toBe(true);
    expect(isOpenPath("/api/auth/callback/azure-ad")).toBe(true);
  });

  /** Ce qui n'est pas nommé est fermé : oublier un écran le protège. */
  it("ferme tout le reste, y compris l'API", () => {
    expect(isOpenPath("/")).toBe(false);
    expect(isOpenPath("/projects")).toBe(false);
    expect(isOpenPath("/api/v1/projects")).toBe(false);
  });
});

describe("la connexion désactivée", () => {
  const initial = { ...process.env };
  afterEach(() => {
    process.env = { ...initial };
  });

  it("s'active en développement, sur un mot exact", () => {
    process.env.AUTH_DISABLED = "true";
    expect(isAuthDisabled()).toBe(true);

    process.env.AUTH_DISABLED = "TRUE";
    expect(isAuthDisabled()).toBe(false);
    process.env.AUTH_DISABLED = "1";
    expect(isAuthDisabled()).toBe(false);
  });

  /** Le drapeau ne doit jamais pouvoir ouvrir la production. */
  it("reste sans effet en production", () => {
    process.env.AUTH_DISABLED = "true";
    Object.defineProperty(process.env, "NODE_ENV", { value: "production" });

    expect(isAuthDisabled()).toBe(false);
  });
});
