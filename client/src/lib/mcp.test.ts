import { describe, expect, it } from "vitest";

import { SCOPES } from "@/lib/api-keys";
import { MCP_CLIENTS, MCP_SCOPES, MCP_TOOLS, MCP_URL } from "@/lib/mcp";

describe("what the MCP tab hands over", () => {
  it("names the address that answers, trailing slash included", () => {
    // `/mcp` redirects to `/mcp/`, and a client that does not follow
    // redirects would be handed an address that never answers.
    expect(MCP_URL).toBe("https://api.ganesh.waat.tools/mcp/");
  });

  it("asks for scopes the form actually offers", () => {
    const offered = SCOPES.map((scope) => scope.value);
    for (const scope of MCP_SCOPES) {
      expect(offered).toContain(scope);
    }
  });

  it("asks for exactly what the tools open, second scopes included", () => {
    // `also` counts: a reader handed the list without it records a review
    // from their terminal and is refused the phase by the key they were
    // given for exactly that.
    const opened = MCP_TOOLS.flatMap((tool) =>
      tool.also ? [tool.scope, tool.also] : [tool.scope],
    );
    expect([...MCP_SCOPES].sort()).toEqual([...new Set(opened)].sort());
  });

  describe("each client's snippet", () => {
    it.each(MCP_CLIENTS)("points $name at the server", (client) => {
      expect(client.snippet).toContain(MCP_URL);
    });

    it.each(MCP_CLIENTS)("leaves $name a key to replace", (client) => {
      // Either the key itself, or the name of the variable carrying it: what
      // no snippet may do is look ready to paste as it stands.
      expect(client.snippet).toMatch(/jns_…|GANESH_API_KEY/);
    });

    it.each(MCP_CLIENTS)("never ships a real key for $name", (client) => {
      expect(client.snippet).not.toMatch(/jns_[A-Za-z0-9]/);
    });
  });
});
