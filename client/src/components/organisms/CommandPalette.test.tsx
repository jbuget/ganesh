import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CommandPalette } from "./CommandPalette";
import { closePalette } from "@/lib/command-palette-store";

const push = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/api/queries", () => ({
  useProjects: () => ({
    missions: [
      {
        project: {
          id: 12,
          label: "Portail bailleurs",
          kind: "project",
          status: "development",
          parent_id: null,
          is_active: true,
        },
      },
      {
        project: {
          id: 40,
          label: "Extranet syndic",
          kind: "project",
          status: "operations",
          parent_id: null,
          is_active: false,
        },
      },
    ],
  }),
  useTeammates: () => ({
    teammates: [
      {
        id: 7,
        display_name: "Léa Chen",
        email: "lea.chen@waat.fr",
        initials: "LC",
        role: "TEAMMATE",
        is_active: true,
      },
    ],
  }),
}));

/** Opens the palette the way anyone does: with the shortcut. */
async function open(who: ReturnType<typeof userEvent.setup>) {
  await who.keyboard("{Meta>}k{/Meta}");
}

describe("CommandPalette", () => {
  beforeEach(() => {
    closePalette();
    push.mockClear();
    window.history.replaceState(null, "", "/kanban");
  });

  it("stays out of the way until it is called for", () => {
    render(<CommandPalette />);

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("opens on the shortcut, showing the screens one can go to", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);

    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Saisie des temps/ }),
    ).toBeInTheDocument();
    // Nothing typed: the projects wait to be asked for.
    expect(screen.queryByRole("option", { name: /Portail bailleurs/ })).toBeNull();
  });

  it("closes on the same shortcut", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await open(who);

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("finds a project by its name, accents aside", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("bailleurs");

    expect(
      screen.getByRole("option", { name: /Portail bailleurs/ }),
    ).toBeInTheDocument();
  });

  it("offers an archived project, and says that it is archived", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("extranet");

    expect(screen.getByRole("option", { name: /Extranet syndic/ })).toHaveTextContent(
      "Archivé",
    );
  });

  it("goes to what is chosen, and closes behind it", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("bailleurs{Enter}");

    expect(push).toHaveBeenCalledWith("/projects/12");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("walks down the list with the arrows", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("{ArrowDown}{Enter}");

    // The second screen of the list, « Accueil » being the first.
    expect(push).toHaveBeenCalledWith("/timesheet");
  });

  it("opens a teammate's panel", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("lea{Enter}");

    expect(push).toHaveBeenCalledWith("/users?user=7");
  });

  it("says so when nothing answers", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("zzzz");

    expect(
      screen.getByText("Rien ne correspond à cette recherche."),
    ).toBeInTheDocument();
  });

  it("opens afresh, rather than on the last search", async () => {
    const who = userEvent.setup();
    render(<CommandPalette />);

    await open(who);
    await who.keyboard("bailleurs");
    await open(who);
    await open(who);

    expect(screen.getByRole("combobox")).toHaveValue("");
  });
});
