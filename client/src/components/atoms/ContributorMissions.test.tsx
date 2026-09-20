import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContributorMissions } from "./ContributorMissions";
import type { MissionShare } from "@/lib/activity";

function a(over: Partial<MissionShare> = {}): MissionShare {
  return { projectId: 1, label: "WAATcher", days: 3, isOffProject: false, ...over };
}

describe("ContributorMissions", () => {
  it("lists what the person put time on, with the days", () => {
    render(<ContributorMissions missions={[a()]} declaredDays={3} />);

    expect(screen.getByText("WAATcher")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
  });

  it("says off-project work is what it is", () => {
    // Five days of which three on leave is not a week spent the way the
    // total alone suggests.
    render(
      <ContributorMissions
        missions={[a({ projectId: 9, label: "Congés", isOffProject: true })]}
        declaredDays={3}
      />,
    );

    expect(screen.getByText("hors projet")).toBeInTheDocument();
  });

  it("agrees the count in the singular", () => {
    render(<ContributorMissions missions={[a()]} declaredDays={3} />);

    expect(screen.getByText("1 projet")).toBeInTheDocument();
  });

  it("agrees the count in the plural", () => {
    render(
      <ContributorMissions
        missions={[a(), a({ projectId: 2, label: "NOMAD", days: 1 })]}
        declaredDays={4}
      />,
    );

    expect(screen.getByText("2 projets")).toBeInTheDocument();
  });

  it("says plainly when there is nothing to break down", () => {
    render(<ContributorMissions missions={[]} declaredDays={0} />);

    expect(screen.getByText("Aucun temps déclaré sur la période.")).toBeInTheDocument();
  });
});
