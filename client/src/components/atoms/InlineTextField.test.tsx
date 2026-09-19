import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { InlineTextField } from "./InlineTextField";

const onChange = vi.fn();

function field(
  value: string | null,
  editable = true,
  validate?: (value: string | null) => string | null,
) {
  render(
    <InlineTextField
      value={value}
      label="Prénom"
      editable={editable}
      validate={validate}
      onChange={onChange}
    />,
  );
}

describe("InlineTextField", () => {
  beforeEach(() => onChange.mockClear());

  it("shows the value it holds", () => {
    field("Léa");

    expect(screen.getByText("Léa")).toBeInTheDocument();
  });

  it("names what is missing rather than showing an empty cell", () => {
    field(null);

    expect(screen.getByRole("button", { name: "Prénom" })).toBeInTheDocument();
  });

  it("writes on Enter", async () => {
    field(null);

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Prénom" }), "Léa{Enter}");

    expect(onChange).toHaveBeenCalledWith("Léa");
  });

  it("empties on a value wiped out", async () => {
    field("Léa");

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.clear(screen.getByRole("textbox", { name: "Prénom" }));
    await userEvent.keyboard("{Enter}");

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("gives up on Escape, leaving the value as it was", async () => {
    field("Léa");

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Prénom" }), "Lé");
    await userEvent.keyboard("{Escape}");

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByText("Léa")).toBeInTheDocument();
  });

  it("writes nothing when nothing changed", async () => {
    field("Léa");

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.keyboard("{Enter}");

    expect(onChange).not.toHaveBeenCalled();
  });

  it("reads without editing when the reader may not write", () => {
    field("Léa", false);

    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText("Léa")).toBeInTheDocument();
  });

  it("says what a refused entry should look like, rather than writing it", async () => {
    field(null, true, () => "Un prénom ne prend pas de chiffre.");

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(
      screen.getByRole("textbox", { name: "Prénom" }),
      "Léa2{Enter}",
    );

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByText("Un prénom ne prend pas de chiffre.")).toBeInTheDocument();
    // Still open on what was typed: correcting it is one keystroke away.
    expect(screen.getByRole("textbox", { name: "Prénom" })).toHaveValue("Léa2");
  });

  it("clears the refusal as soon as the entry changes", async () => {
    field(null, true, (value) => (value === "Léa2" ? "Pas de chiffre." : null));

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(
      screen.getByRole("textbox", { name: "Prénom" }),
      "Léa2{Enter}",
    );
    await userEvent.keyboard("{Backspace}");

    expect(screen.queryByText("Pas de chiffre.")).toBeNull();
  });

  it("shows a write the server refused instead of breaking the screen", async () => {
    onChange.mockRejectedValueOnce(new Error("422"));
    field(null);

    await userEvent.click(screen.getByRole("button", { name: "Prénom" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Prénom" }), "Léa{Enter}");

    expect(await screen.findByText("Enregistrement impossible.")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Prénom" })).toHaveValue("Léa");
  });

  it("says a refusal of the suggestion too, where the suggestion was offered", async () => {
    onChange.mockRejectedValueOnce(new Error("409"));
    render(
      <InlineTextField
        value={null}
        label="Prénom"
        suggestion="lea"
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "lea" }));

    expect(await screen.findByText("Enregistrement impossible.")).toBeInTheDocument();
  });
});
