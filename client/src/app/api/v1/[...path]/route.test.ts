/**
 * The relay carries bytes, not only text.
 *
 * It used to read the body with `text()` and answer with a hard-coded
 * `application/json`: a file went up mangled and came back as a string. What
 * follows is the guarantee that an image survives the round trip in both
 * directions, and that the headers a download needs reach the browser.
 */
import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
  currentSession: vi.fn(),
  needsRefresh: vi.fn(),
  refreshTokens: vi.fn(),
}));

vi.mock("@/lib/auth/session", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/auth/session")>("@/lib/auth/session");
  return { ...actual, currentSession: auth.currentSession };
});
vi.mock("@/lib/auth/entra", () => ({
  needsRefresh: auth.needsRefresh,
  refreshTokens: auth.refreshTokens,
}));

const { GET, POST } = await import("./route");

const PNG = new Uint8Array([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0xff, 0x00,
]);

function upstream(response: Response): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => response),
  );
}

/** What the upstream was called with, whatever the relay did to it. */
function called(): RequestInit & { url: string } {
  const spy = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
  const [url, init] = spy.mock.calls[0];
  return { url, ...(init as RequestInit) };
}

beforeEach(() => {
  vi.clearAllMocks();
  auth.currentSession.mockResolvedValue({ idToken: "jeton", email: "l@waat.fr" });
  auth.needsRefresh.mockReturnValue(false);
});

describe("the BFF relay", () => {
  it("hands back the bytes of a file untouched", async () => {
    upstream(
      new Response(PNG, {
        headers: { "Content-Type": "image/png", "Content-Disposition": "inline" },
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost:3000/api/v1/projects/4/attachments/2/content"),
    );
    const body = new Uint8Array(await response.arrayBuffer());

    expect(body).toEqual(PNG);
    expect(response.headers.get("Content-Type")).toBe("image/png");
  });

  it("carries the headers a download needs", async () => {
    upstream(
      new Response(PNG, {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": 'attachment; filename="note.pdf"',
          "X-Content-Type-Options": "nosniff",
        },
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost:3000/api/v1/projects/4/attachments/2/content"),
    );

    expect(response.headers.get("Content-Disposition")).toBe(
      'attachment; filename="note.pdf"',
    );
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
  });

  it("carries what the API says about reading a file safely", async () => {
    // The file is served to the browser on *this* origin, not the API's: a
    // protection the API sets and this relay drops is one nobody receives.
    upstream(
      new Response(PNG, {
        headers: {
          "Content-Type": "application/octet-stream",
          "Content-Disposition": 'attachment; filename="piege.svg"',
          "Content-Security-Policy": "default-src 'none'",
        },
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost:3000/api/v1/projects/4/attachments/2/content"),
    );

    expect(response.headers.get("Content-Security-Policy")).toBe("default-src 'none'");
  });

  it("sends the bytes of a file up as the browser wrote them", async () => {
    upstream(
      new Response('{"id":1}', { headers: { "Content-Type": "application/json" } }),
    );
    const request = new NextRequest(
      "http://localhost:3000/api/v1/projects/4/attachments",
      {
        method: "POST",
        body: PNG,
        headers: { "Content-Type": "multipart/form-data; boundary=----x" },
      },
    );

    await POST(request);

    // Byte for byte: read as a string, as this used to be, the high bytes of
    // a PNG come back as replacement characters and the file is ruined.
    expect(new Uint8Array(called().body as ArrayBuffer)).toEqual(PNG);
    expect(new Headers(called().headers).get("Content-Type")).toBe(
      "multipart/form-data; boundary=----x",
    );
  });

  it("still relays JSON, and says nothing on a 204", async () => {
    upstream(new Response(null, { status: 204 }));

    const response = await GET(
      new NextRequest("http://localhost:3000/api/v1/projects"),
    );

    expect(response.status).toBe(204);
    expect(await response.text()).toBe("");
  });

  /*
    Caddy sits in front of the API in production and compresses what it
    serves. `fetch` hands back the body decompressed but the headers as they
    came: `Content-Length` then counts the compressed bytes, a few hundred
    where the JSON is a few thousand. Relayed as such, the answer reached the
    browser cut off mid-object — « Réponse illisible », on every screen whose
    answer was big enough to be compressed and small enough to be buffered.
  */
  it("does not relay a length that counts other bytes than the ones it sends", async () => {
    const whole = JSON.stringify({ entries: Array.from({ length: 40 }, (_, i) => i) });
    upstream(
      new Response(whole, {
        headers: {
          "Content-Type": "application/json",
          // What the upstream said of the bytes before they were decompressed.
          "Content-Length": "42",
        },
      }),
    );

    const response = await GET(
      new NextRequest("http://localhost:3000/api/v1/projects/20/audit"),
    );

    expect(response.headers.get("Content-Length")).not.toBe("42");
    expect(await response.text()).toBe(whole);
  });

  it("signs the call with the session it holds", async () => {
    upstream(new Response("[]", { headers: { "Content-Type": "application/json" } }));

    await GET(new NextRequest("http://localhost:3000/api/v1/projects?mission=4"));

    const headers = new Headers(called().headers);
    expect(headers.get("Authorization")).toBe("Bearer jeton");
    expect(called().url).toBe("http://localhost:8000/api/v1/projects?mission=4");
  });
});
