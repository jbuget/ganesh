import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UpdateFeedItem } from "./UpdateFeedItem";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import type { HomeUpdate } from "@/lib/home";

const NOW = new Date("2026-09-19T10:00:00Z");

const entry = (body = "Recette terminée"): HomeUpdate => ({
  item: {
    project: { id: 4, label: "Portail bailleurs" },
  } as ProjectListItemResponse,
  update: {
    author: { id: 9, display_name: "Marie Martin", initials: "MM" },
    body,
    published_at: "2026-09-18T08:00:00Z",
  },
});

describe("UpdateFeedItem", () => {
  it("names the project the message speaks of", () => {
    // The feed mixes several threads: a message read without its project says
    // nothing.
    render(<UpdateFeedItem entry={entry()} now={NOW} onOpen={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("signs the message with its author and its moment", () => {
    render(<UpdateFeedItem entry={entry()} now={NOW} onOpen={vi.fn()} />);

    expect(screen.getByText(/Marie Martin/)).toBeInTheDocument();
    expect(screen.getByText(/hier/)).toBeInTheDocument();
  });

  it("renders the message as markdown, as the thread does", () => {
    render(
      <UpdateFeedItem
        entry={entry("La recette est **terminée**")}
        now={NOW}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText("terminée").tagName).toBe("STRONG");
  });

  it("is reachable with the keyboard, not by the mouse alone", async () => {
    const onOpen = vi.fn();
    render(<UpdateFeedItem entry={entry()} now={NOW} onOpen={onOpen} />);

    await userEvent.tab();
    await userEvent.keyboard("{Enter}");

    expect(onOpen).toHaveBeenCalledWith(4);
  });

  it("opens the thread once when its name is clicked, never twice", async () => {
    const onOpen = vi.fn();
    render(<UpdateFeedItem entry={entry()} now={NOW} onOpen={onOpen} />);

    await userEvent.click(screen.getByRole("button", { name: "Portail bailleurs" }));

    expect(onOpen).toHaveBeenCalledExactlyOnceWith(4);
  });
});
