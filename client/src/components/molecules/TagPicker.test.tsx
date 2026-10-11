import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TagPicker } from "./TagPicker";

const IA = { id: 1, name: "IA", color: "blue" as const, project_count: 4 };
const SUEZ = { id: 2, name: "Suez", color: "red" as const, project_count: 2 };

let suggestions = [IA, SUEZ];
const asked: string[] = [];

vi.mock("@/lib/api/queries", () => ({
  useTags: (search: string) => {
    asked.push(search);
    return { tags: suggestions };
  },
}));

function picker(carried = [SUEZ], handlers = {}) {
  const props = {
    onAdd: vi.fn().mockResolvedValue(undefined),
    onRemove: vi.fn().mockResolvedValue(undefined),
    ...handlers,
  };
  render(
    <TagPicker
      tags={carried.map(({ id, name, color }) => ({ id, name, color }))}
      {...props}
    />,
  );
  return props;
}

async function open() {
  await userEvent.click(screen.getByRole("button", { name: "Ajouter un tag" }));
}

describe("TagPicker", () => {
  beforeEach(() => {
    suggestions = [IA, SUEZ];
    asked.length = 0;
  });

  it("shows the tags the project carries, each in its colour", () => {
    picker();

    expect(screen.getByText("Suez")).toBeInTheDocument();
  });

  it("takes a tag off in one click, without opening anything", async () => {
    const { onRemove } = picker();

    await userEvent.click(screen.getByRole("button", { name: "Retirer le tag Suez" }));

    expect(onRemove).toHaveBeenCalledWith(2);
  });

  it("invites to put the first tag on when there is none", () => {
    picker([]);

    expect(screen.getByRole("button", { name: "Ajouter un tag" })).toHaveTextContent(
      "Ajouter un tag",
    );
  });

  it("offers the tags in use once opened", async () => {
    picker();

    await open();

    expect(screen.getByRole("button", { name: /IA/ })).toBeInTheDocument();
    expect(screen.getByText("4 projets")).toBeInTheDocument();
  });

  it("puts on an existing tag by its name, in one click", async () => {
    const { onAdd } = picker();

    await open();
    await userEvent.click(screen.getByRole("button", { name: /IA/ }));

    expect(onAdd).toHaveBeenCalledWith("IA");
  });

  it("takes off a tag it already carries when it is clicked in the list", async () => {
    const { onRemove } = picker();

    await open();
    await userEvent.click(screen.getByRole("button", { name: /^Suez/, pressed: true }));

    expect(onRemove).toHaveBeenCalledWith(2);
  });

  it("asks for what was typed, to find the closest tags", async () => {
    picker();

    await open();
    await userEvent.type(screen.getByLabelText("Rechercher un tag"), "sue");

    expect(asked).toContain("sue");
  });

  it("offers to open a tag nobody has opened", async () => {
    suggestions = [];
    const { onAdd } = picker([]);

    await open();
    await userEvent.type(screen.getByLabelText("Rechercher un tag"), "Frigo");
    await userEvent.click(
      screen.getByRole("button", { name: "Créer le tag « Frigo »" }),
    );

    expect(onAdd).toHaveBeenCalledWith("Frigo");
  });

  it("does not offer to open a tag that already says the same", async () => {
    suggestions = [IA];
    picker([]);

    await open();
    await userEvent.type(screen.getByLabelText("Rechercher un tag"), "ia");

    expect(
      screen.queryByRole("button", { name: /Créer le tag/ }),
    ).not.toBeInTheDocument();
  });

  it("opens the tag with the Enter key when only that can be done", async () => {
    suggestions = [];
    const { onAdd } = picker([]);

    await open();
    await userEvent.type(screen.getByLabelText("Rechercher un tag"), "Frigo{Enter}");

    expect(onAdd).toHaveBeenCalledWith("Frigo");
  });

  it("clears the field once a tag is put on", async () => {
    suggestions = [];
    picker([]);

    await open();
    const field = screen.getByLabelText("Rechercher un tag");
    await userEvent.type(field, "Frigo{Enter}");

    expect(field).toHaveValue("");
  });

  it("says why when the server refuses, in French", async () => {
    const { ApiError } = await import("@/lib/api/fetcher");
    const refuses = vi
      .fn()
      .mockRejectedValue(new ApiError(422, "A mission carries 8 tags at most."));
    picker([], { onAdd: refuses });

    await open();
    await userEvent.click(screen.getByRole("button", { name: /IA/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Un projet porte 8 tags au plus.",
    );
  });

  it("carries the pointer cursor on what is clickable", () => {
    picker();

    expect(screen.getByRole("button", { name: "Ajouter un tag" }).className).toContain(
      "cursor-pointer",
    );
  });
});
