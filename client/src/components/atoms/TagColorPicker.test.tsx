import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TagColorPicker } from "./TagColorPicker";

function picker(value: "blue" | "red" = "blue", onChange = vi.fn()) {
  render(
    <TagColorPicker value={value} label="Couleur du tag Suez" onChange={onChange} />,
  );
  return onChange;
}

describe("TagColorPicker", () => {
  it("shows the colour the tag has, under the name the screen gives it", () => {
    picker();

    expect(
      screen.getByRole("button", { name: "Couleur du tag Suez" }),
    ).toBeInTheDocument();
  });

  it("offers the whole palette once opened, each colour by its name", async () => {
    picker();

    await userEvent.click(screen.getByRole("button", { name: "Couleur du tag Suez" }));

    for (const name of ["Rouge", "Violet", "Citron vert", "Turquoise", "Rose"]) {
      expect(screen.getByRole("button", { name })).toBeInTheDocument();
    }
  });

  it("marks the colour the tag already has", async () => {
    picker("red");

    await userEvent.click(screen.getByRole("button", { name: "Couleur du tag Suez" }));

    expect(
      screen.getByRole("button", { name: "Rouge", pressed: true }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Bleu", pressed: false }),
    ).toBeInTheDocument();
  });

  it("reports the colour chosen, and closes", async () => {
    const onChange = picker();

    await userEvent.click(screen.getByRole("button", { name: "Couleur du tag Suez" }));
    await userEvent.click(screen.getByRole("button", { name: "Violet" }));

    expect(onChange).toHaveBeenCalledWith("violet");
    expect(screen.queryByRole("button", { name: "Violet" })).not.toBeInTheDocument();
  });

  it("carries the pointer cursor on what is clickable", () => {
    picker();

    expect(
      screen.getByRole("button", { name: "Couleur du tag Suez" }).className,
    ).toContain("cursor-pointer");
  });
});
