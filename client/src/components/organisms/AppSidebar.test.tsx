import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppSidebar } from "./AppSidebar";

const pathname = vi.hoisted(() => ({ value: "/" }));
type User = {
  display_name: string;
  email: string;
  initials: string;
  role: string;
};

const JEREMY: User = {
  display_name: "Jérémy Buget",
  email: "j.buget@waat.fr",
  initials: "JB",
  role: "MANAGER",
};

const user = vi.hoisted(() => ({
  value: {
    display_name: "Jérémy Buget",
    email: "j.buget@waat.fr",
    initials: "JB",
    role: "MANAGER",
  } as
    { display_name: string; email: string; initials: string; role: string } | undefined,
}));

vi.mock("next/navigation", () => ({ usePathname: () => pathname.value }));
vi.mock("@/lib/api/queries", () => ({
  useCurrentUser: () => ({ user: user.value }),
}));
// Ending the session is checked in `lib/use-deconnexion.test.ts`: here, only
// the bar that offers it matters.
vi.mock("@/lib/use-sign-out", () => ({ useSignOut: () => vi.fn() }));
// Same for the inbox: what the bell shows is checked where the bell is, and
// the bar is only answering for having one.
vi.mock("@/lib/use-inbox", () => ({
  useInbox: () => ({
    entries: [],
    unreadCount: 0,
    isSettling: false,
    toggleRead: vi.fn(),
    markAllRead: vi.fn(),
  }),
}));

describe("AppSidebar", () => {
  it("offers to fold the bar", () => {
    render(<AppSidebar />);

    expect(
      screen.getByRole("button", { name: "Replier la barre latérale" }),
    ).toBeInTheDocument();
  });

  it("keeps the labels readable to screen readers once folded", async () => {
    render(<AppSidebar />);

    await userEvent.click(
      screen.getByRole("button", { name: "Replier la barre latérale" }),
    );

    // The labels disappear to the eye, never from the accessibility tree.
    expect(screen.getByRole("link", { name: /Saisie des temps/ })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Déplier la barre latérale" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("offers every screen", () => {
    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /Accueil/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Saisie des temps/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Projets/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Planification/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Statistiques/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Utilisateurs/ })).toBeInTheDocument();
  });

  it("closes the navigation with « Statistiques »", () => {
    render(<AppSidebar />);

    const labels = screen.getAllByRole("link").map((link) => link.textContent);

    expect(labels.at(-1)).toMatch(/Statistiques/);
  });

  it("opens the navigation with « Accueil », which holds the root", () => {
    render(<AppSidebar />);

    const labels = screen.getAllByRole("link").map((link) => link.textContent);

    expect(labels[0]).toMatch(/Accueil/);
    expect(screen.getByRole("link", { name: /Accueil/ })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /Saisie des temps/ })).toHaveAttribute(
      "href",
      "/timesheet",
    );
  });

  it("flags the current screen to screen readers", () => {
    pathname.value = "/";
    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /Accueil/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: /Projets/ })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("follows the page shown", () => {
    pathname.value = "/projects";
    render(<AppSidebar />);

    expect(screen.getByRole("link", { name: /Projets/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("shows the current user at the foot", () => {
    render(<AppSidebar />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
  });

  it("flags the manager role", () => {
    user.value = JEREMY;
    render(<AppSidebar />);

    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("shows no role for a teammate", () => {
    user.value = {
      display_name: "L. Chen",
      email: "l.chen@waat.fr",
      initials: "LC",
      role: "TEAMMATE",
    };
    render(<AppSidebar />);

    expect(screen.queryByText("Manager")).toBeNull();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("shrinks the name to its initials in the avatar", () => {
    user.value = { ...JEREMY, role: "TEAMMATE" };
    render(<AppSidebar />);

    expect(screen.getByText("JB")).toBeInTheDocument();
  });

  it("shows no user block while the identity is unknown", () => {
    user.value = undefined;
    render(<AppSidebar />);

    expect(screen.queryByText(/Buget|Chen/)).toBeNull();
  });

  it("offers the palette, and says which keys open it", () => {
    render(<AppSidebar />);

    // Which keys they are depends on the keyboard one is on, and the name
    // says them either way: a shortcut nobody is shown is one nobody uses.
    expect(
      screen.getByRole("button", { name: /^Rechercher \(.+\)$/ }),
    ).toBeInTheDocument();
  });

  // A short screen used to push the foot of the bar below the fold: the name
  // and the way out simply were not there. The bar is held to the height of
  // the window, as `PageLayout` holds the screen beside it, and the tabs
  // scroll inside it.
  it("holds itself to the height of the window", () => {
    render(<AppSidebar />);

    const bar = screen.getByRole("complementary");

    expect(bar.className).toContain("h-screen");
  });

  it("scrolls its tabs rather than pushing the foot off the screen", () => {
    render(<AppSidebar />);

    const tabs = screen.getByRole("navigation", { name: "Navigation principale" });

    expect(tabs.className).toContain("overflow-y-auto");
    // Without it a flex child refuses to shrink under its content, and the
    // overflow never happens.
    expect(tabs.className).toContain("min-h-0");
  });
});
