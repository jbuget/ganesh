import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SharedGazettePage } from "./SharedGazettePage";
import type { PublicDigestResponse } from "@/lib/api/generated/model";

const read = vi.hoisted(() => ({
  digest: undefined as PublicDigestResponse | undefined,
  isLoading: false,
  isError: false,
}));

vi.mock("@/lib/api/queries", () => ({ useSharedDigest: () => read }));

function aDigest(over: Partial<PublicDigestResponse> = {}): PublicDigestResponse {
  return {
    month: "2026-09-01",
    version: 5,
    generated_at: "2026-10-09T11:50:00",
    prose: "Ganesh est passé en exploitation.",
    prose_model: "gemini-3.8-flash",
    spotlights: [
      {
        project_id: 7,
        label: "Ganesh",
        text: "Un registre des temps.",
        status: "operations",
        went_live: true,
        updates_posted: 9,
        days_declared: 0,
        contributors: 0,
      },
    ],
    tally: {
      projects_created: 15,
      projects_archived: 6,
      phase_changes: 15,
      news_posted: 138,
      months_validated: 1,
      requests_filed: 0,
      requests_converted: 0,
    },
    went_live: ["Ganesh"],
    names: ["Ganesh", "NOMAD - Formulaire en ligne"],
    ...over,
  };
}

beforeEach(() => {
  read.digest = aDigest();
  read.isLoading = false;
  read.isError = false;
});

describe("SharedGazettePage", () => {
  it("says which month and which version it reads", () => {
    render(<SharedGazettePage token="tok" />);

    expect(
      screen.getByRole("heading", { name: /La Gazette · septembre 2026/i }),
    ).toBeVisible();
    expect(screen.getByText(/Version 5, du 9 octobre 2026/)).toBeVisible();
  });

  it("tells the narrative and the projects under the spotlight", () => {
    render(<SharedGazettePage token="tok" />);

    expect(screen.getByText("Sous le projecteur")).toBeVisible();
    expect(screen.getByText("Un registre des temps.")).toBeVisible();
  });

  it("sets in bold the projects it names", () => {
    render(<SharedGazettePage token="tok" />);

    expect(
      [...document.querySelectorAll("strong")].map((node) => node.textContent),
    ).toContain("Ganesh");
  });

  it("sets in bold the projects the server says the text names, short form included", () => {
    read.digest = aDigest({ prose: "Ganesh avance, et NOMAD recule." });

    render(<SharedGazettePage token="tok" />);

    expect(
      [...document.querySelectorAll("strong")].map((node) => node.textContent),
    ).toEqual(expect.arrayContaining(["Ganesh", "NOMAD"]));
  });

  it("lists what went live, by name", () => {
    render(<SharedGazettePage token="tok" />);

    expect(screen.getByText("Ganesh est passé en exploitation")).toBeVisible();
  });

  it("offers nothing to do: no button, no link back into the application", () => {
    render(<SharedGazettePage token="tok" />);

    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryAllByRole("link")).toHaveLength(0);
  });

  it("says only that a link opens nothing, whether it was closed or never existed", () => {
    read.digest = undefined;
    read.isError = true;

    render(<SharedGazettePage token="tok" />);

    expect(screen.getByText(/n'ouvre rien, ou il n'est plus valable/)).toBeVisible();
  });

  it("says it is loading rather than a link is closed", () => {
    read.digest = undefined;
    read.isLoading = true;

    render(<SharedGazettePage token="tok" />);

    expect(screen.getByText("Chargement…")).toBeVisible();
    expect(screen.queryByText(/n'ouvre rien/)).toBeNull();
  });
});
