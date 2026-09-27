/**
 * Starting a borrowing asks the API first, and writes nothing if it says no.
 *
 * That is the whole caution of this handler. Sealing a cookie on the strength
 * of a click would hand back a session every request of which the API
 * refuses — a screen that draws nothing, with no band on it to say why.
 */
import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({ currentSession: vi.fn() }));

vi.mock("@/lib/auth/session", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/auth/session")>("@/lib/auth/session");
  return { ...actual, currentSession: auth.currentSession };
});

const { POST, DELETE } = await import("./route");
const { IMPERSONATION_COOKIE } = await import("@/lib/auth/impersonation");

function upstream(response: Response): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => response),
  );
}

function asking(body: unknown): NextRequest {
  return new NextRequest("http://localhost:3000/api/auth/impersonate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  process.env.SESSION_SECRET = "a development session key, long enough";
  auth.currentSession.mockResolvedValue({ idToken: "jeton", email: "a@waat.fr" });
});

describe("starting a borrowing", () => {
  it("seals the account the API agreed to", async () => {
    upstream(new Response(JSON.stringify({ id: 42 })));

    const response = await POST(asking({ userId: 42 }));

    expect(response.status).toBe(200);
    expect(response.cookies.get(IMPERSONATION_COOKIE)?.value).toBeTruthy();
  });

  it("tries it on the one route that answers for whoever is reading", async () => {
    upstream(new Response(JSON.stringify({ id: 42 })));

    await POST(asking({ userId: 42 }));

    const [url, init] = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(String(url)).toContain("/users/me");
    expect(
      new Headers((init as RequestInit).headers).get("x-impersonate-user-id"),
    ).toBe("42");
  });

  it("writes nothing down when the API refuses", async () => {
    // A manager clicking their way here, or an account since deactivated.
    upstream(
      new Response(JSON.stringify({ detail: "Réservé aux administrateurs." }), {
        status: 403,
      }),
    );

    const response = await POST(asking({ userId: 42 }));

    expect(response.status).toBe(403);
    expect(response.cookies.get(IMPERSONATION_COOKIE)).toBeUndefined();
  });

  it("relays what the API said, so the screen shows the reason", async () => {
    upstream(
      new Response(JSON.stringify({ detail: "Ce compte est désactivé." }), {
        status: 403,
      }),
    );

    const said = (await (await POST(asking({ userId: 42 }))).json()) as {
      detail: string;
    };

    expect(said.detail).toBe("Ce compte est désactivé.");
  });

  it("asks the API nothing when no teammate was named", async () => {
    upstream(new Response("{}"));

    const response = await POST(asking({ userId: "quarante-deux" }));

    expect(response.status).toBe(400);
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });
});

describe("ending one", () => {
  it("gives the account back by expiring the cookie", async () => {
    const response = await DELETE();

    expect(response.status).toBe(204);
    expect(response.cookies.get(IMPERSONATION_COOKIE)?.value).toBe("");
  });
});
