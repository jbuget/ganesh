import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { InlineTextArea } from "./InlineTextArea";

describe("InlineTextArea", () => {
  it("writes what was typed when the field is left", async () => {
    const onChange = vi.fn();
    render(<InlineTextArea value={null} label="Problème" onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: "Problème" }));
    await userEvent.type(screen.getByRole("textbox"), "Tapées une par une.");
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith("Tapées une par une.");
  });

  it("reads a field of spaces as unsaid", async () => {
    const onChange = vi.fn();
    render(
      <InlineTextArea value="Quelque chose" label="Problème" onChange={onChange} />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Problème" }));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("says nothing was filled in rather than leaving a blank", () => {
    render(
      <InlineTextArea
        value={null}
        label="Problème"
        editable={false}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Non renseigné")).toBeInTheDocument();
  });
});
