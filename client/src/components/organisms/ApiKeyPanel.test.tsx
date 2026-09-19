import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiKeyPanel } from "@/components/organisms/ApiKeyPanel";
import type { ApiKeyResponse } from "@/lib/api/generated/model";

const person = { id: 1, display_name: "Toni DA RODDA", initials: "TD" };

const key = (overrides: Partial<ApiKeyResponse> = {}) =>
  ({
    id: 7,
    name: "CI waat-tools",
    masked: "jns_abcdef123456",
    scopes: ["catalog:read"],
    owner: person,
    created_by: { id: 2, display_name: "Jérémy BUGET", initials: "JB" },
    created_at: "2026-01-15T10:00:00",
    expires_at: "2027-01-15T10:00:00",
    last_used_at: null,
    revoked_at: null,
    revoked_by: null,
    state: "active",
    ...overrides,
  }) as unknown as ApiKeyResponse;

function panel(overrides: Partial<ApiKeyResponse> = {}, editable = true) {
  const handlers = {
    onRename: vi.fn().mockResolvedValue(undefined),
    onChangeScopes: vi.fn().mockResolvedValue(undefined),
    onRevoke: vi.fn().mockResolvedValue(undefined),
    onClose: vi.fn(),
  };
  render(<ApiKeyPanel apiKey={key(overrides)} editable={editable} {...handlers} />);
  return handlers;
}

describe("ApiKeyPanel", () => {
  it("names the key and shows its public half", () => {
    panel();
    expect(screen.getByText("CI waat-tools")).toBeInTheDocument();
    expect(screen.getByText("jns_abcdef123456")).toBeInTheDocument();
  });

  it("says who answers for the machine and who minted it", () => {
    panel();
    expect(screen.getByText("Toni DA RODDA")).toBeInTheDocument();
    expect(screen.getByText("Jérémy BUGET")).toBeInTheDocument();
  });

  it("closes on the cross", async () => {
    const { onClose } = panel();
    await userEvent.click(screen.getByRole("button", { name: "Fermer" }));
    expect(onClose).toHaveBeenCalled();
  });

  describe("renaming", () => {
    it("offers the pencil to a manager", () => {
      panel();
      expect(
        screen.getByRole("button", { name: "Renommer la clé" }),
      ).toBeInTheDocument();
    });

    it("sends the new name", async () => {
      const { onRename } = panel();

      await userEvent.click(screen.getByRole("button", { name: "Renommer la clé" }));
      const field = screen.getByRole("textbox");
      await userEvent.clear(field);
      await userEvent.type(field, "CI waat.tools{Enter}");

      expect(onRename).toHaveBeenCalledWith(7, "CI waat.tools");
    });

    it("offers nothing to a teammate", () => {
      panel({}, false);
      expect(
        screen.queryByRole("button", { name: "Renommer la clé" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("scopes", () => {
    it("lets a manager change what the key opens", async () => {
      const { onChangeScopes } = panel();

      await userEvent.click(screen.getByRole("checkbox", { name: /Temps/ }));

      expect(onChangeScopes).toHaveBeenCalledWith(7, ["catalog:read", "entries:read"]);
    });

    it("sends only what a broad scope does not already carry", async () => {
      const { onChangeScopes } = panel();

      await userEvent.click(screen.getByRole("checkbox", { name: /Tous \(lecture\)/ }));

      expect(onChangeScopes).toHaveBeenCalledWith(7, ["all:read"]);
    });

    it("shows a teammate what it opens, without a box to tick", () => {
      panel({}, false);
      expect(screen.getByText("Catalogue (lecture)")).toBeInTheDocument();
      expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    });
  });

  describe("a key that is already cut", () => {
    const revoked = {
      state: "revoked",
      revoked_at: "2026-06-01T10:00:00",
      revoked_by: { id: 2, display_name: "Jérémy BUGET", initials: "JB" },
    };

    it("says when it was cut and by whom", () => {
      panel(revoked);
      expect(screen.getByText(/par Jérémy BUGET/)).toBeInTheDocument();
    });

    it("cannot be renamed: it is a piece of the audit", () => {
      panel(revoked);
      expect(
        screen.queryByRole("button", { name: "Renommer la clé" }),
      ).not.toBeInTheDocument();
    });

    it("cannot have its scopes changed either", () => {
      panel(revoked);
      expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    });

    it("offers no revocation, having had one", () => {
      panel(revoked);
      expect(
        screen.queryByRole("button", { name: "Révoquer la clé" }),
      ).not.toBeInTheDocument();
    });
  });

  it("lets an expired key be renamed, for whoever reads the table", () => {
    panel({ state: "expired" });
    expect(screen.getByRole("button", { name: "Renommer la clé" })).toBeInTheDocument();
  });

  describe("revoking", () => {
    it("asks before cutting", async () => {
      const { onRevoke } = panel();

      await userEvent.click(screen.getByRole("button", { name: "Révoquer la clé" }));

      expect(screen.getByText(/immédiate et définitive/i)).toBeInTheDocument();
      expect(onRevoke).not.toHaveBeenCalled();
    });

    it("cuts once confirmed", async () => {
      const { onRevoke } = panel();

      await userEvent.click(screen.getByRole("button", { name: "Révoquer la clé" }));
      await userEvent.click(screen.getByRole("button", { name: "Révoquer" }));

      expect(onRevoke).toHaveBeenCalledWith(7);
    });

    it("is offered to a manager only", () => {
      panel({}, false);
      expect(
        screen.queryByRole("button", { name: "Révoquer la clé" }),
      ).not.toBeInTheDocument();
    });
  });

  it("never shows a secret", () => {
    // There is nothing to reveal: the panel carries the public half alone.
    panel();
    expect(screen.queryByText(/jns_abcdef123456_/)).not.toBeInTheDocument();
  });
});
