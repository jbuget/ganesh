import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SharePanel } from "./SharePanel";
import type { ShareLinkResponse } from "@/lib/api/generated/model";

const share = vi.hoisted(() => ({
  links: [] as ShareLinkResponse[],
  isLoading: false,
  isOpening: false,
  addressOf: (token: string) => `https://ganesh.waat.tools/p/gazette/${token}`,
  open: vi.fn(),
  close: vi.fn(),
}));

vi.mock("@/lib/use-share-links", () => ({ useShare: () => share }));

const LINK: ShareLinkResponse = {
  id: 4,
  token: "tok",
  created_by: "Léa Chen",
  created_at: "2026-10-11T09:00:00",
};

beforeEach(() => {
  vi.clearAllMocks();
  share.links = [];
  share.isOpening = false;
});

async function opened() {
  render(<SharePanel month="2026-09-01" version={5} />);
  await userEvent.click(screen.getByRole("button", { name: /Partager/ }));
}

describe("SharePanel", () => {
  it("says what a link gives before asking for anything", async () => {
    await opened();

    expect(screen.getByText("Partager la version 5")).toBeVisible();
    expect(screen.getByText(/ne peut rien faire d'autre/)).toBeVisible();
    expect(screen.getByText(/jusqu'à ce que quelqu'un le ferme/)).toBeVisible();
  });

  it("opens a link on the version on screen", async () => {
    await opened();

    await userEvent.click(screen.getByRole("button", { name: "Créer un lien" }));

    expect(share.open).toHaveBeenCalledTimes(1);
  });

  it("lists the links still open, with who opened each", async () => {
    share.links = [LINK];

    await opened();

    expect(screen.getByLabelText("Adresse du lien")).toHaveValue(
      "https://ganesh.waat.tools/p/gazette/tok",
    );
    expect(screen.getByText(/Ouvert par Léa Chen/)).toBeVisible();
  });

  it("names nobody for a link whose author is gone", async () => {
    share.links = [{ ...LINK, created_by: null }];

    await opened();

    expect(screen.getByText(/Ouvert par un ancien membre/)).toBeVisible();
  });

  it("closes a link from its own line", async () => {
    share.links = [LINK];
    await opened();

    await userEvent.click(screen.getByRole("button", { name: "Fermer le lien" }));

    expect(share.close).toHaveBeenCalledWith(4);
  });

  it("does not offer a second click while a link is being made", async () => {
    share.isOpening = true;

    await opened();

    expect(screen.getByRole("button", { name: "Création…" })).toBeDisabled();
  });
});
