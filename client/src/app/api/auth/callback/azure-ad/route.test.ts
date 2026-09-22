/**
 * What the callback says out loud when Entra turns somebody away.
 *
 * A refusal Entra decides on its own — an application nobody consented to, a
 * person not assigned to it — comes back as an `error` in the query string,
 * and the whole of the diagnosis is in `error_description`: the AADSTS code.
 * Dropped, as it was, the only trace left of a colleague who cannot sign in
 * is the word « denied » in an address bar.
 */
import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

const { GET } = await import("./route");

afterEach(() => {
  vi.restoreAllMocks();
});

function callbackWith(query: string): NextRequest {
  return new NextRequest(`http://localhost:3000/api/auth/callback/azure-ad?${query}`);
}

describe("the Entra callback", () => {
  it("writes down what Entra refused, and why", async () => {
    const logged = vi.spyOn(console, "error").mockImplementation(() => {});

    await GET(
      callbackWith(
        "error=access_denied&error_description=" +
          encodeURIComponent("AADSTS50105: The signed in user is not assigned"),
      ),
    );

    expect(logged).toHaveBeenCalledWith(
      expect.stringContaining("[auth]"),
      "access_denied",
      expect.stringContaining("AADSTS50105"),
    );
  });

  it("still sends the person back to sign in, saying no more than « denied »", async () => {
    // The description names the tenant and the application: it is for the
    // logs, never for whoever is standing at the door.
    vi.spyOn(console, "error").mockImplementation(() => {});

    const response = await GET(
      callbackWith("error=access_denied&error_description=AADSTS50105"),
    );

    const location = new URL(response.headers.get("location") ?? "");
    expect(location.pathname).toBe("/sign-in");
    expect(location.searchParams.get("reason")).toBe("denied");
    expect(response.headers.get("location")).not.toContain("AADSTS");
  });
});
