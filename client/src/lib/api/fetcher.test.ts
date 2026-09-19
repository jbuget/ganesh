import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, bffFetcher } from "./fetcher";

function respondWith(body: string, init: ResponseInit) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, init)));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("bffFetcher", () => {
  it("returns the payload of a successful call", async () => {
    respondWith('{"id":1}', { status: 200 });

    await expect(bffFetcher("/api/v1/projects")).resolves.toMatchObject({
      data: { id: 1 },
      status: 200,
    });
  });

  it("carries the API's own message when it explains itself in JSON", async () => {
    respondWith('{"detail":"Mois déjà validé"}', { status: 409 });

    await expect(bffFetcher("/api/v1/months")).rejects.toMatchObject({
      status: 409,
      detail: "Mois déjà validé",
    });
  });

  /**
   * A 500 from FastAPI comes back as plain text, and a gateway may answer in
   * HTML. Parsing before reading the status turned both into a `SyntaxError`
   * pointing at the fetcher, which said nothing of the call that failed.
   */
  it("keeps the status when the error body is not JSON", async () => {
    respondWith("Internal Server Error", {
      status: 500,
      statusText: "Internal Server Error",
    });

    await expect(bffFetcher("/api/v1/planning/simulations")).rejects.toMatchObject({
      name: "ApiError",
      status: 500,
      detail: "Internal Server Error",
    });
  });

  it("reports a successful call whose body is not JSON rather than parsing it", async () => {
    respondWith("<html>proxied away</html>", { status: 200, statusText: "OK" });

    await expect(bffFetcher("/api/v1/projects")).rejects.toBeInstanceOf(ApiError);
  });

  /* jsdom refuses to build a 204: the status forbids a body. The branch under
     test is the empty body itself, which a 200 carries just as well. */
  it("accepts an empty body, as a call that returns nothing sends", async () => {
    respondWith("", { status: 200 });

    await expect(bffFetcher("/api/v1/entries")).resolves.toMatchObject({
      data: undefined,
      status: 200,
    });
  });
});
