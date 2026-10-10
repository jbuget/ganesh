import { render, renderHook, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const back = vi.fn();
const push = vi.fn();
const pathname = { value: "/projects/12" };

vi.mock("next/navigation", () => ({
  usePathname: () => pathname.value,
  useRouter: () => ({ back, push }),
}));
const invalidateQueries = vi.fn();

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries }),
}));
// The sheet itself is read elsewhere: here only the way out of it matters, and
// a mission that cannot be found draws the header and nothing else. What the
// page hands the sheet is kept, to check what a write does to the cache.
const written: { call?: () => void | Promise<void> } = {};

vi.mock("@/lib/use-project-detail", () => ({
  useProjectDetail: (_projectId: number, onWrite?: () => void | Promise<void>) => {
    written.call = onWrite;
    return { detail: null, notFound: true };
  },
}));

import { forgetTrail, useNavigationTrail } from "@/lib/navigation-trail";

import { ProjectDetailPage } from "./ProjectDetailPage";

/** Crosses the screens, as the sidebar does above every one of them. */
function landOn(screen: string) {
  pathname.value = screen;
  const trail = renderHook(() => useNavigationTrail());

  return {
    then(next: string) {
      pathname.value = next;
      trail.rerender();
      return this;
    },
  };
}

beforeEach(() => {
  forgetTrail();
  back.mockClear();
  push.mockClear();
  invalidateQueries.mockClear();
});

describe("ProjectDetailPage", () => {
  it("goes back to the screen the sheet was opened from", async () => {
    landOn("/kanban").then("/projects/12");

    render(<ProjectDetailPage projectId={12} />);
    await userEvent.click(screen.getByRole("button", { name: "Retour" }));

    expect(back).toHaveBeenCalled();
  });

  it("offers the reference list to whoever landed straight on the sheet", () => {
    // A link shared in a message, a new tab: going back would leave Ganesh.
    // A named destination is drawn as the link it is, openable beside the sheet.
    landOn("/projects/12");

    render(<ProjectDetailPage projectId={12} />);

    expect(screen.getByRole("link", { name: "Projets" })).toHaveAttribute(
      "href",
      "/projects",
    );
    expect(screen.queryByRole("button", { name: "Projets" })).not.toBeInTheDocument();
  });

  it("empties the cache after a write, so no screen reads a stale mission", async () => {
    // A mission deleted from its own page was still in the reference list on
    // the way back: nothing told the screens to read again.
    landOn("/projects/12");

    render(<ProjectDetailPage projectId={12} />);
    await written.call?.();

    expect(invalidateQueries).toHaveBeenCalled();
  });
});
