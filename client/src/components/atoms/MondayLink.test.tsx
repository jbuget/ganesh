import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MondayLink } from "./MondayLink";
import type { ProjectResponse } from "@/lib/api/generated/model";

const mission = (kind: string, is_syncable_to_monday: boolean): ProjectResponse =>
  ({
    id: 1,
    label: "X",
    kind,
    parent_id: null,
    statut: null,
    actif: true,
    estime_j: null,
    is_syncable_to_monday,
  }) as ProjectResponse;

describe("MondayLink", () => {
  it("signale une mission rattachée", () => {
    render(<MondayLink project={mission("projet", true)} />);

    expect(screen.getByText("Rattaché")).toBeInTheDocument();
  });

  it("signale une mission qui ne remontera pas dans Monday", () => {
    render(<MondayLink project={mission("projet", false)} />);

    expect(screen.getByText("Non rattaché")).toBeInTheDocument();
  });

  it("n'affiche rien pour une activité hors projet, jamais synchronisée", () => {
    render(<MondayLink project={mission("hors_projet", false)} />);

    expect(screen.queryByText(/rattach/i)).toBeNull();
  });
});
