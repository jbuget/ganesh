import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { InlineTextField } from "./InlineTextField";

const onChange = vi.fn();

function field(value: string | null, editable = true) {
  render(
    <InlineTextField
      value={value}
      label="Prénom"
      editable={editable}
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
});
