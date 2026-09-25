import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProfilePage } from "./ProfilePage";
import type { UserResponse } from "@/lib/api/generated/model";
import { A_WEEK_ON_SITE } from "@/lib/presence";

const profile = vi.hoisted(() => ({ state: {} as Record<string, unknown> }));

// The reading of « may this person write? » is its own hook, and its own
// tests: here it is answered yes, so that what is under test stays what the
// file says it is.
const mayWrite = vi.hoisted(() => ({ value: true }));
vi.mock("@/lib/use-may-write", () => ({ useMayWrite: () => mayWrite.value }));

vi.mock("@/lib/use-profile", () => ({ useProfileScreen: () => profile.state }));

const USER = {
  id: 1,
  email: "l.chen@waat.fr",
  display_name: "Léa Chen",
  initials: "LC",
  role: "TEAMMATE",
  is_active: true,
  department: "information_systems",
  presence: A_WEEK_ON_SITE,
  reminder_cadence: "DAILY",
} as UserResponse;

function show(overrides: Record<string, unknown> = {}) {
  profile.state = {
    user: USER,
    isLoading: false,
    isSaving: false,
    choose: vi.fn(),
    ...overrides,
  };
  render(<ProfilePage />);
  return profile.state;
}

describe("ProfilePage", () => {
  it("names the screen and what it is for", () => {
    show();

    expect(screen.getByText("Mon profil")).toBeInTheDocument();
    expect(screen.getByText(/comment il vous écrit/)).toBeInTheDocument();
  });

  it("shows who one is, without offering to change it", () => {
    show();

    expect(screen.getByText("Léa Chen")).toBeInTheDocument();
    expect(screen.getByText("l.chen@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Collaborateur")).toBeInTheDocument();
    expect(screen.getByText("Système d'information")).toBeInTheDocument();
    expect(screen.getByText(/demandez à un manager/)).toBeInTheDocument();
  });

  it("says so rather than leaving a blank when nobody has given a pôle", () => {
    show({ user: { ...USER, department: null } });

    expect(screen.getByText("Non renseigné")).toBeInTheDocument();
  });

  it("shows the cadence in force", () => {
    show({ user: { ...USER, reminder_cadence: "WEEKLY" } });

    expect(screen.getByLabelText(/Chaque semaine/)).toBeChecked();
  });

  it("says why a letter exists beside the bell", () => {
    show();

    expect(
      screen.getByText(/La cloche ne prévient que si Ganesh est ouvert/),
    ).toBeInTheDocument();
  });

  it("records the cadence one picks", async () => {
    const state = show();

    await userEvent.click(screen.getByLabelText(/Jamais/));

    expect(state.choose).toHaveBeenCalledWith("NEVER");
  });

  it("says a choice is on its way rather than looking idle", () => {
    show({ isSaving: true });

    expect(screen.getByText("Enregistrement…")).toBeInTheDocument();
  });

  it("waits rather than showing an empty profile", () => {
    show({ user: undefined, isLoading: true });

    expect(screen.getByText("Chargement…")).toBeInTheDocument();
  });
});
