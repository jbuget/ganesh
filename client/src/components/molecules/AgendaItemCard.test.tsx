import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AgendaItemCard } from "./AgendaItemCard";
import type { FlaggedUpdateResponse } from "@/lib/api/generated/model";

const NOW = new Date("2026-09-26T10:00:00Z");

function anItem(over: Partial<FlaggedUpdateResponse> = {}): FlaggedUpdateResponse {
  return {
    update_id: 1,
    project_id: 10,
    project_label: "Portail",
    body: "Le sponsor attend une date.",
    author: { id: 7, display_name: "L. Chen", initials: "LC" },
    published_at: "2026-09-21T09:00:00Z",
    raised_by: { id: 8, display_name: "N. Garo", initials: "NG" },
    flagged_at: "2026-09-22T09:00:00Z",
    ...over,
  };
}

/**
 * Whether the text overflows is measured on what was drawn, and jsdom draws
 * nothing: both heights are stubbed so the fold can be tested at all.
 */
function drawnAs(scrollHeight: number, clientHeight: number) {
  for (const [name, value] of [
    ["scrollHeight", scrollHeight],
    ["clientHeight", clientHeight],
  ] as const) {
    Object.defineProperty(HTMLElement.prototype, name, {
      configurable: true,
      get: () => value,
    });
  }
}

afterEach(() => {
  vi.restoreAllMocks();
  for (const name of ["scrollHeight", "clientHeight"]) {
    Object.defineProperty(HTMLElement.prototype, name, {
      configurable: true,
      get: () => 0,
    });
  }
});

describe("AgendaItemCard", () => {
  it("names the author and who raised it", () => {
    render(<AgendaItemCard item={anItem()} now={NOW} />);

    expect(screen.getByText("L. Chen")).toBeInTheDocument();
    expect(screen.getByText(/Signalé par N. Garo/)).toBeInTheDocument();
  });

  it("offers nothing to fold on an update that fits", () => {
    drawnAs(80, 192);

    render(<AgendaItemCard item={anItem()} now={NOW} />);

    expect(
      screen.queryByRole("button", { name: /Lire la suite/ }),
    ).not.toBeInTheDocument();
  });

  /**
   * An agenda is a list one reads down: one update running to three screens
   * buries the four lines under it.
   */
  it("folds a long update, and unfolds it on demand", async () => {
    drawnAs(900, 192);

    render(<AgendaItemCard item={anItem({ body: "Une longue revue." })} now={NOW} />);
    await userEvent.click(screen.getByRole("button", { name: /Lire la suite/ }));

    expect(screen.getByRole("button", { name: /Replier/ })).toBeInTheDocument();
  });

  it("lowers the mark on the gesture", async () => {
    const onClear = vi.fn();

    render(<AgendaItemCard item={anItem()} now={NOW} onClear={onClear} />);
    await userEvent.click(screen.getByRole("button", { name: "Discuté" }));

    expect(onClear).toHaveBeenCalled();
  });

  it("offers no gesture without one to offer", () => {
    render(<AgendaItemCard item={anItem()} now={NOW} />);

    expect(screen.queryByRole("button", { name: "Discuté" })).not.toBeInTheDocument();
  });
});
