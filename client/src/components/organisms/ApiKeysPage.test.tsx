import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiKeysPage } from "@/components/organisms/ApiKeysPage";
import type { ApiKeyResponse } from "@/lib/api/generated/model";

const person = { id: 1, display_name: "Toni DA RODDA", initials: "TD" };

const key = (overrides: Partial<ApiKeyResponse> = {}) =>
  ({
    id: 1,
    name: "CI waat-tools",
    masked: "jns_abcdef123456",
    scopes: ["catalog:read"],
    owner: person,
    created_by: person,
    created_at: "2026-01-01T10:00:00",
    expires_at: null,
    last_used_at: null,
    revoked_at: null,
    revoked_by: null,
    state: "active",
    ...overrides,
  }) as unknown as ApiKeyResponse;

const screenState = {
  keys: [key()],
  isLoading: false,
  isManager: true,
  minted: null,
  opened: null as ApiKeyResponse | null,
  now: new Date("2026-09-19T12:00:00"),
  create: vi.fn(),
  dismissMinted: vi.fn(),
  open: vi.fn(),
  close: vi.fn(),
  rename: vi.fn(),
  changeScopes: vi.fn(),
  revoke: vi.fn(),
};

vi.mock("@/lib/use-api-keys", () => ({
  useApiKeysScreen: () => screenState,
}));

vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({ teammates: [{ id: 1, display_name: "Toni DA RODDA" }] }),
}));

function view(state: Partial<typeof screenState> = {}) {
  Object.assign(screenState, {
    keys: [key()],
    isLoading: false,
    isManager: true,
    minted: null,
    opened: null,
    ...state,
  });
  render(<ApiKeysPage />);
}

describe("ApiKeysPage", () => {
  it("shows a key by its name and its public half", () => {
    view();
    expect(screen.getByText("CI waat-tools")).toBeInTheDocument();
    expect(screen.getByText("jns_abcdef123456")).toBeInTheDocument();
  });

  it("names the person who answers for the machine", () => {
    view();
    expect(screen.getByText("Toni DA RODDA")).toBeInTheDocument();
  });

  it("reads the scopes in French", () => {
    view();
    expect(screen.getByText("Catalogue (lecture)")).toBeInTheDocument();
  });

  describe("what a teammate may do", () => {
    it("reads the table", () => {
      view({ isManager: false });
      expect(screen.getByText("CI waat-tools")).toBeInTheDocument();
    });

    it("is offered nothing to create", () => {
      view({ isManager: false });
      expect(
        screen.queryByRole("button", { name: "Créer une clé" }),
      ).not.toBeInTheDocument();
    });

    it("opens a key beside the list, to read it", async () => {
      view({ isManager: false, open: vi.fn() });

      await userEvent.click(screen.getByText("CI waat-tools"));

      expect(screenState.open).toHaveBeenCalledWith(1);
    });

    it("sees an empty state with nothing to click", () => {
      view({ isManager: false, keys: [] });
      expect(screen.getByText("Aucune clé.")).toBeInTheDocument();
    });
  });

  describe("what a manager may do", () => {
    it("is offered the creation", () => {
      view();
      expect(screen.getByRole("button", { name: "Créer une clé" })).toBeInTheDocument();
    });

    it("reads what a key is for before being shown the button", () => {
      view({ keys: [] });
      expect(screen.getByText(/service externe/i)).toBeInTheDocument();
    });

    it("opens a key beside the list, to correct it", async () => {
      view({ open: vi.fn() });

      await userEvent.click(screen.getByText("CI waat-tools"));

      expect(screenState.open).toHaveBeenCalledWith(1);
    });
  });

  describe("the panel that shows a fresh key", () => {
    const token = "jns_abcdef123456_theSecretPart";

    it("stays shut while nothing was minted", () => {
      view();
      expect(
        screen.queryByText(/ne sera plus jamais affichée/i),
      ).not.toBeInTheDocument();
    });

    it("says the key will never be shown again", () => {
      view({ minted: { key: key(), token } as never });
      expect(screen.getByText(/ne sera plus jamais affichée/i)).toBeInTheDocument();
    });

    it("shows the whole token, once", () => {
      view({ minted: { key: key(), token } as never });
      expect(screen.getByText(token)).toBeInTheDocument();
    });

    it("closing it is what loses the token", async () => {
      const dismiss = vi.fn();
      view({ minted: { key: key(), token } as never, dismissMinted: dismiss });

      await userEvent.click(screen.getByRole("button", { name: /j'ai copié/i }));

      expect(dismiss).toHaveBeenCalled();
    });
  });

  it("never shows a secret in the table itself", () => {
    // There is no « reveal »: the row carries the public half and nothing else.
    view();
    expect(screen.queryByText(/theSecretPart/)).not.toBeInTheDocument();
  });
});
