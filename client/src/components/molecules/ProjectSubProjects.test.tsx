import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProjectSubProjects } from "./ProjectSubProjects";
import type { ProjectResponse } from "@/lib/api/generated/model";

const workPackage = (id: number, label: string, status = "scoping"): ProjectResponse =>
  ({ id, label, status, kind: "work_package", parent_id: 10 }) as ProjectResponse;

describe("ProjectSubProjects", () => {
  it("announces that no sub-project is attached", () => {
    render(<ProjectSubProjects subProjects={[]} />);

    expect(screen.getByText("Aucun sous-projet")).toBeInTheDocument();
  });

  it("leads to the sheet of each sub-project", () => {
    render(<ProjectSubProjects subProjects={[workPackage(11, "Authentification")]} />);

    expect(screen.getByRole("link", { name: /Authentification/ })).toHaveAttribute(
      "href",
      "/projets/11",
    );
  });

  it("says the phase of each sub-project", () => {
    render(
      <ProjectSubProjects
        subProjects={[
          workPackage(11, "Authentification"),
          workPackage(12, "Reprise", "development"),
        ]}
      />,
    );

    expect(screen.getByText("Cadrage")).toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });
});
