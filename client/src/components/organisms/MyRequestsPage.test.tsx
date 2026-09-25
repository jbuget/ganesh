import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { RequestResponse } from "@/lib/api/generated/model";

import { MyRequestsPage } from "./MyRequestsPage";

const screenState = vi.hoisted(() => ({
  requests: [] as RequestResponse[],
  isLoading: false,
  opened: null as RequestResponse | null,
  open: vi.fn(),
  close: vi.fn(),
  file: vi.fn(),
  fillIn: vi.fn(),
  submit: vi.fn(),
  withdraw: vi.fn(),
  remove: vi.fn(),
}));

vi.mock("@/lib/use-my-requests", () => ({
  useMyRequestsScreen: () => ({
    ...screenState,
    find: (id: number) =>
      screenState.requests.find((request) => request.id === id) ?? null,
  }),
}));

// The panel is held by the URL, on this screen as on the team's: a need one
// has open is a need one can send to somebody.
vi.mock("@/lib/opened-request", () => ({
  useOpenedRequest: () => ({
    openedRequest: screenState.opened?.id ?? null,
    open: screenState.open,
    close: screenState.close,
  }),
}));

vi.mock("@/lib/api/queries", () => ({
  useRequestSponsors: () => ({ sponsors: [{ id: 3, label: "C. Direction" }] }),
}));

const DRAFT: RequestResponse = {
  id: 1,
  title: "Relances de paiement à la main",
  state: "draft",
  requester: { id: 7, label: "Anne Métier" },
  sponsors: [{ id: 3, label: "C. Direction" }],
  departments: ["finance_admin"],
  created_at: "2026-09-22T10:00:00Z",
};

describe("MyRequestsPage", () => {
  beforeEach(() => {
    screenState.requests = [];
    screenState.opened = null;
    screenState.open.mockClear();
  });

  it("says what the screen is for when nothing has been asked yet", () => {
    render(<MyRequestsPage />);

    expect(screen.getByText(/Aucune demande/)).toBeInTheDocument();
  });

  it("lists what one asked for, and where it stands", () => {
    screenState.requests = [DRAFT];

    render(<MyRequestsPage />);

    expect(screen.getByText("Relances de paiement à la main")).toBeInTheDocument();
    expect(screen.getByText("Brouillon")).toBeInTheDocument();
    expect(screen.getByText(/Administratif & Financier/)).toBeInTheDocument();
  });

  it("opens the one that was clicked", async () => {
    screenState.requests = [DRAFT];

    render(<MyRequestsPage />);
    await userEvent.click(screen.getByRole("button", { name: /Relances/ }));

    expect(screenState.open).toHaveBeenCalledWith(1);
  });

  it("says what a draft still lacks before it may be handed over", () => {
    screenState.requests = [DRAFT];
    screenState.opened = DRAFT;

    render(<MyRequestsPage />);

    expect(
      screen.getByText(
        "Il manque le problème, qui est concerné et le résultat attendu avant de pouvoir soumettre.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Soumettre" })).toBeDisabled();
  });

  it("hands over a need that says enough", async () => {
    const complete: RequestResponse = {
      ...DRAFT,
      problem: "Tapées une par une.",
      impact: "Trois personnes.",
      expected_outcome: "Une relance automatique.",
    };
    screenState.requests = [complete];
    screenState.opened = complete;

    render(<MyRequestsPage />);
    await userEvent.click(screen.getByRole("button", { name: "Soumettre" }));

    expect(screenState.submit).toHaveBeenCalledWith(1);
  });

  it("stops the sheet moving once it has been handed over", () => {
    const handed: RequestResponse = { ...DRAFT, state: "submitted" };
    screenState.requests = [handed];
    screenState.opened = handed;

    render(<MyRequestsPage />);

    expect(screen.queryByRole("button", { name: "Soumettre" })).toBeNull();
    // The label says what the gesture costs: « Modifier » alone would let
    // somebody fix a typo and put their need to sleep without knowing.
    expect(
      screen.getByRole("button", { name: "Reprendre pour modifier" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/retire de la file d'arbitrage/)).toBeInTheDocument();
    // The fields no longer offer themselves: what is being weighed stops moving.
    expect(screen.queryByRole("button", { name: "Le problème" })).toBeNull();
  });

  it("gives the reader the motive behind a refusal", () => {
    const refused: RequestResponse = {
      ...DRAFT,
      state: "rejected",
      decision_note: "Déjà couvert par l'extranet.",
      decided_by: { id: 1, label: "J. Buget" },
      decided_at: "2026-09-25T09:00:00Z",
    };
    screenState.requests = [refused];
    screenState.opened = refused;

    render(<MyRequestsPage />);

    const panel = within(screen.getByRole("complementary"));
    expect(panel.getByText("Refusée")).toBeInTheDocument();
    expect(panel.getByText("Déjà couvert par l'extranet.")).toBeInTheDocument();
    expect(panel.getByText("J. Buget", { exact: false })).toBeInTheDocument();
  });
});
