import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { InlineNumberField } from "./InlineNumberField";

const baseProps = {
  suffix: "jrs.",
  label: "Estimer",
  onChange: vi.fn(),
};

describe("InlineNumberField", () => {
  /**
   * An estimate of 23.5 days read « 23.5 jrs. », with an English point, right
   * beside a consumed figure written « 8,75 » with a French comma.
   */
  it("writes a fractional value the French way at rest", () => {
    render(<InlineNumberField {...baseProps} value={23.5} />);

    expect(screen.getByRole("button")).toHaveTextContent("23,5 jrs.");
  });

  it("leaves a whole number without a needless decimal", () => {
    render(<InlineNumberField {...baseProps} value={20} />);

    expect(screen.getByRole("button")).toHaveTextContent("20 jrs.");
  });

  it("invites an entry when there is no value yet", () => {
    render(<InlineNumberField {...baseProps} value={null} />);

    expect(screen.getByRole("button")).toHaveTextContent("Estimer");
  });

  it("opens on the raw value, which is what parses back", async () => {
    render(<InlineNumberField {...baseProps} value={23.5} />);

    await userEvent.click(screen.getByRole("button"));

    expect(screen.getByRole("textbox")).toHaveValue("23.5");
  });

  /**
   * The value is shown « 23,5 », so that is what somebody retypes. It has to
   * be taken — otherwise the field would read back what it refuses.
   */
  it("takes a French comma back", async () => {
    const onChange = vi.fn();
    render(<InlineNumberField {...baseProps} onChange={onChange} value={20} />);

    await userEvent.click(screen.getByRole("button"));
    await userEvent.clear(screen.getByRole("textbox"));
    await userEvent.type(screen.getByRole("textbox"), "23,5{Enter}");

    expect(onChange).toHaveBeenCalledWith(23.5);
  });
});
