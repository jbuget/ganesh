import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";

import { useReadAs } from "./use-read-as";

const router = vi.hoisted(() => ({ replace: vi.fn(), refresh: vi.fn() }));
const queryClient = vi.hoisted(() => ({ clear: vi.fn() }));
const me = vi.hoisted(() => ({ current: null as Record<string, unknown> | null }));

vi.mock("next/navigation", () => ({ useRouter: () => router }));
vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => queryClient }));
vi.mock("@/lib/api/queries", () => ({ useCurrentUser: () => ({ user: me.current }) }));

function answering(response: Response) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

describe("useReadAs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    me.current = { id: 1, display_name: "L. Chen", impersonated_by: null };
  });

  it("knows nobody is borrowing when the account is read by its owner", () => {
    const { result } = renderHook(() => useReadAs());

    expect(result.current.isBorrowing).toBe(false);
    expect(result.current.borrower).toBeNull();
  });

  it("names who is reading, when it is not the account's owner", () => {
    me.current = {
      id: 2,
      display_name: "L. Chen",
      impersonated_by: { id: 1, display_name: "Jérémy Buget" },
    };
    const { result } = renderHook(() => useReadAs());

    expect(result.current.isBorrowing).toBe(true);
    expect(result.current.borrower).toEqual({ id: 1, display_name: "Jérémy Buget" });
  });

  it("opens an account through the handler, never through the API", () => {
    // What it moves is a sealed cookie, and only a Route Handler writes one.
    answering(new Response("{}"));
    const { result } = renderHook(() => useReadAs());

    return result.current.readAs(42).then(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/auth/impersonate",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ userId: 42 }),
        }),
      );
    });
  });

  it("clears the cache before drawing anything as somebody else", async () => {
    // Without this, a screen loaded as the administrator would show for the
    // length of a reload under the teammate's name.
    answering(new Response("{}"));
    const { result } = renderHook(() => useReadAs());

    await result.current.readAs(42);

    expect(queryClient.clear).toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith("/");
  });

  it("hands back what the handler said when it refuses, and goes nowhere", async () => {
    answering(
      new Response(JSON.stringify({ detail: "Ce compte est désactivé." }), {
        status: 403,
      }),
    );
    const { result } = renderHook(() => useReadAs());

    expect(await result.current.readAs(42)).toBe("Ce compte est désactivé.");
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("gives the account back, and lands where one left from", async () => {
    answering(new Response(null, { status: 204 }));
    const { result } = renderHook(() => useReadAs());

    await result.current.giveBack();

    expect(fetch).toHaveBeenCalledWith("/api/auth/impersonate", { method: "DELETE" });
    expect(queryClient.clear).toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith("/users");
  });
});
