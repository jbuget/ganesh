import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserActivityTab } from "./UserActivityTab";

/**
 * The three sections have their own tests: what is asked here is that the tab
 * reads the record of the teammate it was opened on, and puts them in order.
 */
const record = vi.hoisted(() => ({
  current: null as unknown,
  loading: false,
}));

vi.mock("@/lib/api/queries", () => ({
  useUserRecord: () => ({ record: record.current, isLoading: record.loading }),
}));

const emptyRecord = {
  user_id: 1,
  missions: [],
  declared: { since: "2026-08-19", until: "2026-09-17", days: 0, missions: [] },
  months: [],
};

const NOW = new Date("2026-09-17T10:00:00Z");

beforeEach(() => {
  record.current = emptyRecord;
  record.loading = false;
});

describe("UserActivityTab", () => {
  it("gives what the teammate carries, in the order one reads it", () => {
    record.current = {
      ...emptyRecord,
      missions: [
        { project_id: 4, label: "WAATcher", status: "development", is_lead: true },
      ],
      declared: {
        since: "2026-08-19",
        until: "2026-09-17",
        days: 2,
        missions: [
          { project_id: 4, label: "WAATcher", days: 2, is_off_project: false },
        ],
      },
      months: [
        {
          month: "2026-09-01",
          delivered: 11,
          forecast: 0,
          working_days: 22,
          elapsed_working_days: 13,
          state: "open",
          validated_at: null,
        },
      ],
    };

    render(<UserActivityTab userId={1} now={NOW} />);

    expect(
      screen.getAllByRole("heading").map((heading) => heading.textContent),
    ).toEqual(["Projets", "Temps déclaré", "Feuilles de temps"]);
    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
  });

  it("says a teammate carries no project rather than leaving a blank", () => {
    render(<UserActivityTab userId={1} now={NOW} />);

    expect(screen.getByText("Aucun projet")).toBeInTheDocument();
  });

  it("says the record is on its way rather than showing an empty one", () => {
    record.current = null;
    record.loading = true;

    render(<UserActivityTab userId={1} now={NOW} />);

    expect(screen.getByText("Chargement…")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Projets" })).toBeNull();
  });
});
