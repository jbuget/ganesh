import { describe, expect, it } from "vitest";

import type { UsersView } from "@/lib/use-users-view";

/** What the hook reads out of an address, without the router around it. */
function viewOf(query: string): UsersView {
  const asked = new URLSearchParams(query).get("vue");
  return asked === "presence" ? "presence" : "comptes";
}

describe("which tab an address opens on", () => {
  it("opens on the accounts when nothing is asked", () => {
    expect(viewOf("")).toBe("comptes");
  });

  it("opens on the week when the address says so", () => {
    // What the home screen hands over: a link that lands on the right tab.
    expect(viewOf("vue=presence")).toBe("presence");
  });

  it("falls back on the accounts for anything it does not know", () => {
    expect(viewOf("vue=n-importe-quoi")).toBe("comptes");
  });
});
