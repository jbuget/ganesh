import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CreateApiKeyDialog } from "@/components/molecules/CreateApiKeyDialog";
import type { UserResponse } from "@/lib/api/generated/model";

const TEAM = [
  { id: 1, display_name: "Toni DA RODDA" },
  { id: 2, display_name: "Jérémy BUGET" },
] as unknown as UserResponse[];

function dialog(onCreate = vi.fn().mockResolvedValue(undefined)) {
  render(
    <CreateApiKeyDialog
      open
      onOpenChange={vi.fn()}
      teammates={TEAM}
      onCreate={onCreate}
    />,
  );
  return onCreate;
}

describe("CreateApiKeyDialog", () => {
  it("asks for the account the key is tied to", () => {
    dialog();
    expect(screen.getByLabelText("Compte associé")).toBeInTheDocument();
  });

  it("says the key dies with that account", () => {
    dialog();
    expect(screen.getByText(/cesse de fonctionner/i)).toBeInTheDocument();
  });

  it("offers every scope, read and write alike", () => {
    dialog();
    for (const label of [
      "Tous (lecture)",
      "Tous (écriture)",
      "Catalogue (lecture)",
      "Projets (lecture)",
      "Projets (écriture)",
      "Temps (lecture)",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("holds the creation back until it has what it needs", () => {
    dialog();
    expect(screen.getByRole("button", { name: "Créer la clé" })).toBeDisabled();
  });

  describe("what a broad scope carries", () => {
    it("leaves every box open while none is broad", () => {
      dialog();
      for (const box of screen.getAllByRole("checkbox")) {
        expect(box).toBeEnabled();
        expect(box).not.toBeChecked();
      }
    });

    it("ticks and locks every read under « Tous (lecture) »", async () => {
      dialog();

      await userEvent.click(screen.getByRole("checkbox", { name: /Tous \(lecture\)/ }));

      for (const name of [/Catalogue/, /Projets \(lecture\)/, /Temps \(lecture\)/]) {
        const box = screen.getByRole("checkbox", { name });
        expect(box).toBeChecked();
        expect(box).toBeDisabled();
      }
    });

    it("says where a locked box gets its right from", async () => {
      dialog();

      await userEvent.click(screen.getByRole("checkbox", { name: /Tous \(lecture\)/ }));

      expect(
        screen.getAllByText("Inclus dans « Tous (lecture) »").length,
      ).toBeGreaterThan(0);
    });

    it("leaves a write open under « Tous (lecture) »", async () => {
      dialog();

      await userEvent.click(screen.getByRole("checkbox", { name: /Tous \(lecture\)/ }));

      const write = screen.getByRole("checkbox", { name: /Projets \(écriture\)/ });
      expect(write).toBeEnabled();
      expect(write).not.toBeChecked();
    });

    it("ticks and locks the writes under « Tous (écriture) », and only them", async () => {
      dialog();

      await userEvent.click(
        screen.getByRole("checkbox", { name: /Tous \(écriture\)/ }),
      );

      const write = screen.getByRole("checkbox", { name: /Projets \(écriture\)/ });
      expect(write).toBeChecked();
      expect(write).toBeDisabled();

      const read = screen.getByRole("checkbox", { name: /Catalogue/ });
      expect(read).toBeEnabled();
      expect(read).not.toBeChecked();
    });

    it("never lets one « Tous » lock the other", async () => {
      // Otherwise ticking both would trap the first one checked and
      // unremovable — which is exactly what it did.
      dialog();
      const read = screen.getByRole("checkbox", { name: /Tous \(lecture\)/ });
      const write = screen.getByRole("checkbox", { name: /Tous \(écriture\)/ });

      await userEvent.click(read);
      await userEvent.click(write);

      expect(read).toBeEnabled();
      expect(write).toBeEnabled();
    });

    it("lets the first « Tous » be unticked after the second", async () => {
      dialog();
      const read = screen.getByRole("checkbox", { name: /Tous \(lecture\)/ });

      await userEvent.click(read);
      await userEvent.click(
        screen.getByRole("checkbox", { name: /Tous \(écriture\)/ }),
      );
      await userEvent.click(read);

      expect(read).not.toBeChecked();
      expect(screen.getByRole("checkbox", { name: /Catalogue/ })).toBeEnabled();
    });

    it("lets a broad scope be unticked again", async () => {
      dialog();
      const broad = screen.getByRole("checkbox", { name: /Tous \(lecture\)/ });

      await userEvent.click(broad);
      await userEvent.click(broad);

      expect(screen.getByRole("checkbox", { name: /Catalogue/ })).toBeEnabled();
    });
  });

  it("exposes the picker under its own name", () => {
    // Base UI does not open under jsdom, as `MissionSelector.test.tsx` already
    // notes: what the menu holds is checked in the browser. What matters here
    // is that the field is the shared picker, named for this form.
    dialog();
    expect(
      screen.getByRole("combobox", { name: "Compte associé" }),
    ).toBeInTheDocument();
  });

  it("carries the name typed into it", async () => {
    dialog();

    await userEvent.type(screen.getByLabelText("Nom"), "CI waat-tools");

    expect(screen.getByLabelText("Nom")).toHaveValue("CI waat-tools");
  });

  it("offers a year ahead rather than imposing one", () => {
    dialog();

    const offered = screen.getByLabelText("Expiration") as HTMLInputElement;
    const year = new Date().getFullYear() + 1;
    expect(offered.value.startsWith(String(year))).toBe(true);
  });
});
