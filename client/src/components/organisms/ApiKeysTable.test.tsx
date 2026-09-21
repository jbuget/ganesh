import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiKeysTable } from "@/components/organisms/ApiKeysTable";
import type { ApiKeyResponse } from "@/lib/api/generated/model";

const key = (overrides: Partial<ApiKeyResponse> = {}) =>
  ({
    id: 7,
    name: "CI waat-tools",
    masked: "jns_abcdef123456",
    scopes: ["catalog:read"],
    owner: { id: 1, display_name: "Toni DA RODDA", initials: "TD" },
    created_by: { id: 2, display_name: "Jérémy BUGET", initials: "JB" },
    created_at: "2026-01-15T09:00:00Z",
    expires_at: null,
    last_used_at: null,
    revoked_at: null,
    revoked_by: null,
    state: "active",
    ...overrides,
  }) as unknown as ApiKeyResponse;

describe("ApiKeysTable", () => {
  it("dates the key and names whoever minted it", () => {
    render(<ApiKeysTable keys={[key()]} onOpen={vi.fn()} />);

    expect(screen.getByRole("columnheader", { name: "Création" })).toBeInTheDocument();
    expect(screen.getByText("15 janv. 2026")).toBeInTheDocument();
    expect(screen.getByText("par Jérémy BUGET")).toBeInTheDocument();
  });
});
