import { afterEach, describe, expect, it } from "vitest";

import { isAuthDisabled, isOpenPath } from "./guard";

describe("the open addresses", () => {
  it("lets the sign-in screen through, and what signing in needs", () => {
    expect(isOpenPath("/sign-in")).toBe(true);
    expect(isOpenPath("/api/auth/login")).toBe(true);
    expect(isOpenPath("/api/auth/callback/azure-ad")).toBe(true);
  });

  /** What is not named is closed: forgetting a screen protects it. */
  it("closes everything else, the API included", () => {
    expect(isOpenPath("/")).toBe(false);
    expect(isOpenPath("/projects")).toBe(false);
    expect(isOpenPath("/api/v1/projects")).toBe(false);
  });
});

describe("sign-in switched off", () => {
  const initial = { ...process.env };
  afterEach(() => {
    process.env = { ...initial };
  });

  it("turns on in development, on an exact word", () => {
    process.env.AUTH_DISABLED = "true";
    expect(isAuthDisabled()).toBe(true);

    process.env.AUTH_DISABLED = "TRUE";
    expect(isAuthDisabled()).toBe(false);
    process.env.AUTH_DISABLED = "1";
    expect(isAuthDisabled()).toBe(false);
  });

  /** The flag must never be able to open production. */
  it("has no effect in production", () => {
    process.env.AUTH_DISABLED = "true";
    Object.defineProperty(process.env, "NODE_ENV", { value: "production" });

    expect(isAuthDisabled()).toBe(false);
  });
});
