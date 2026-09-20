import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserDeclaredDays } from "./UserDeclaredDays";
import type { DeclaredWindowResponse } from "@/lib/api/generated/model";

const window_ = (
  overrides: Partial<DeclaredWindowResponse> = {},
): DeclaredWindowResponse => ({
  since: "2026-08-19",
  until: "2026-09-17",
  days: 0,
  missions: [],
  ...overrides,
});

describe("UserDeclaredDays", () => {
  it("says the stretch it was read over, even with nothing in it", () => {
    render(<UserDeclaredDays declared={window_()} />);

    expect(screen.getByText(/Aucun temps déclaré/)).toBeInTheDocument();
    expect(screen.getByText("du 19 août au 17 sept.")).toBeInTheDocument();
  });

  it("names each project and what it received", () => {
    render(
      <UserDeclaredDays
        declared={window_({
          days: 2,
          missions: [
            {
              project_id: 1,
              label: "WAATcher",
              days: 1.5,
              is_off_project: false,
            },
            { project_id: 2, label: "Congés", days: 0.5, is_off_project: true },
          ],
        })}
      />,
    );

    expect(screen.getByText("WAATcher")).toBeInTheDocument();
    expect(screen.getByText("1,5 j")).toBeInTheDocument();
    expect(screen.getByText("0,5 j")).toBeInTheDocument();
  });

  it("names off-project work as such", () => {
    render(
      <UserDeclaredDays
        declared={window_({
          days: 1,
          missions: [{ project_id: 2, label: "Congés", days: 1, is_off_project: true }],
        })}
      />,
    );

    expect(screen.getByText("hors projet")).toBeInTheDocument();
  });

  it("adds up how many projects the time went to", () => {
    render(
      <UserDeclaredDays
        declared={window_({
          days: 3,
          missions: [
            { project_id: 1, label: "WAATcher", days: 2, is_off_project: false },
            { project_id: 2, label: "Ganesh", days: 1, is_off_project: false },
          ],
        })}
      />,
    );

    expect(screen.getByText("2 projets")).toBeInTheDocument();
    expect(screen.getByText("3 j")).toBeInTheDocument();
  });

  it("agrees with a single project", () => {
    render(
      <UserDeclaredDays
        declared={window_({
          days: 1,
          missions: [
            { project_id: 1, label: "WAATcher", days: 1, is_off_project: false },
          ],
        })}
      />,
    );

    expect(screen.getByText("1 projet")).toBeInTheDocument();
  });
});
