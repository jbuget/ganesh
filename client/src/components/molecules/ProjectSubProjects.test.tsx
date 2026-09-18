import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProjectSubProjects } from "./ProjectSubProjects";
import type { ProjectResponse } from "@/lib/api/generated/model";

const lot = (id: number, label: string, status = "scoping"): ProjectResponse =>
  ({ id, label, status, kind: "work_package", parent_id: 10 }) as ProjectResponse;

describe("ProjectSubProjects", () => {
  it("annonce qu'aucun sous-projet n'est rattaché", () => {
    render(<ProjectSubProjects sousProjets={[]} />);

    expect(screen.getByText("Aucun sous-projet")).toBeInTheDocument();
  });

  it("mène à la fiche de chaque sous-projet", () => {
    render(<ProjectSubProjects sousProjets={[lot(11, "Authentification")]} />);

    expect(screen.getByRole("link", { name: /Authentification/ })).toHaveAttribute(
      "href",
      "/projets/11",
    );
  });

  it("dit la phase de chaque sous-projet", () => {
    render(
      <ProjectSubProjects
        sousProjets={[lot(11, "Authentification"), lot(12, "Reprise", "development")]}
      />,
    );

    expect(screen.getByText("Cadrage")).toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });
});
