import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TagManagerDialog } from "./TagManagerDialog";

let tags = [
  { id: 1, name: "Suez", color: "red", project_count: 3 },
  { id: 2, name: "Suez Env", color: "blue", project_count: 1 },
];
const management = vi.hoisted(() => ({
  rename: vi.fn(),
  recolor: vi.fn(),
  merge: vi.fn(),
}));

vi.mock("@/lib/api/queries", () => ({
  useTags: () => ({ tags }),
}));
vi.mock("@/lib/use-tag-management", () => ({
  useTagManagement: () => management,
}));

beforeEach(() => {
  vi.clearAllMocks();
  tags = [
    { id: 1, name: "Suez", color: "red", project_count: 3 },
    { id: 2, name: "Suez Env", color: "blue", project_count: 1 },
  ];
  for (const call of Object.values(management)) call.mockResolvedValue(undefined);
});

const open = () => render(<TagManagerDialog open onOpenChange={() => {}} />);

describe("TagManagerDialog", () => {
  it("says what looking after the tags changes", () => {
    open();

    expect(screen.getByRole("dialog")).toHaveTextContent(
      "change tous les projets qui le portent",
    );
  });

  it("lists every tag in use, with how many projects carry it", () => {
    open();

    expect(screen.getByText("Suez Env")).toBeInTheDocument();
    expect(screen.getByText("3 projets")).toBeInTheDocument();
    expect(screen.getByText("1 projet")).toBeInTheDocument();
  });

  it("renames a tag through the hook, by its id", async () => {
    open();

    await userEvent.click(screen.getByRole("button", { name: "Nom du tag Suez Env" }));
    const field = screen.getByLabelText("Nom du tag Suez Env");
    await userEvent.clear(field);
    await userEvent.type(field, "Suez Group{Enter}");

    expect(management.rename).toHaveBeenCalledWith(2, "Suez Group");
  });

  it("recolours a tag through the hook, by its id", async () => {
    open();

    await userEvent.click(screen.getByRole("button", { name: "Couleur du tag Suez" }));
    await userEvent.click(screen.getByRole("button", { name: "Violet" }));

    expect(management.recolor).toHaveBeenCalledWith(1, "violet");
  });

  it("folds a tag into the one chosen, by their ids", async () => {
    open();

    await userEvent.click(
      screen.getByRole("button", { name: "Fusionner Suez Env dans…" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^Suez\b(?! Env)/ }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmer la fusion" }));

    expect(management.merge).toHaveBeenCalledWith(2, 1);
  });

  it("says so when no tag is in use yet", () => {
    tags = [];
    open();

    expect(
      screen.getByText("Aucun tag n'est posé pour l'instant."),
    ).toBeInTheDocument();
  });

  it("is not drawn while closed", () => {
    render(<TagManagerDialog open={false} onOpenChange={() => {}} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
