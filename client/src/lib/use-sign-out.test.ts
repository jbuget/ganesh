import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";

import { useSignOut } from "./use-sign-out";

const router = vi.hoisted(() => ({ replace: vi.fn(), refresh: vi.fn() }));
const queryClient = vi.hoisted(() => ({ clear: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => router }));
vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => queryClient }));

describe("useSignOut", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
  });

  it("asks the server to clear the session", async () => {
    const { result } = renderHook(() => useSignOut());

    await result.current();

    expect(fetch).toHaveBeenCalledWith("/api/auth/signout", { method: "POST" });
  });

  it("clears the cache before sending back home", async () => {
    const { result } = renderHook(() => useSignOut());

    await result.current();

    // Without this, the next screen would show again the data of the person who
    // has just left, for the length of a reload.
    expect(queryClient.clear).toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith("/");
    expect(router.refresh).toHaveBeenCalled();
  });
});
