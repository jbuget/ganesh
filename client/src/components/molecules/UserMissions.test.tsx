import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserMissions } from "./UserMissions";
import type { RecordedMissionResponse } from "@/lib/api/generated/model";

const mission = (
  overrides: Partial<RecordedMissionResponse> = {},
): RecordedMissionResponse => ({
  project_id: 1,
  label: "WAATcher",
  status: "development",
  is_lead: false,
  ...overrides,
});

describe("UserMissions", () => {
  it("announces that nobody put this teammate on a project", () => {
    render(<UserMissions missions={[]} />);

    expect(screen.getByText("Aucun projet")).toBeInTheDocument();
  });

  it("names the project and the phase it is in", () => {
    render(<UserMissions missions={[mission()]} />);

    expect(screen.getByText("WAATcher")).toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });

  it("says who answers for a project, beyond working on it", () => {
    render(<UserMissions missions={[mission({ is_lead: true })]} />);

    expect(screen.getByText("Référent")).toBeInTheDocument();
  });

  it("stays silent on a contributor", () => {
    render(<UserMissions missions={[mission()]} />);

    expect(screen.queryByText("Référent")).not.toBeInTheDocument();
  });

  it("leads to the project's own sheet", () => {
    render(<UserMissions missions={[mission({ project_id: 12 })]} />);

    expect(screen.getByRole("link", { name: /WAATcher/ })).toHaveAttribute(
      "href",
      "/projects/12",
    );
  });

  it("draws off-project work, which carries no phase", () => {
    render(<UserMissions missions={[mission({ label: "Congés", status: null })]} />);

    expect(screen.getByText("Congés")).toBeInTheDocument();
  });
});
