import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TagListField } from "@/components/atoms/TagListField";

function field(values: string[] = [], onChange = vi.fn()) {
  render(
    <TagListField
      values={values}
      label="Stack"
      placeholder="Next.js"
      onChange={onChange}
    />,
  );
  return onChange;
}

describe("TagListField", () => {
  it("shows what it holds", () => {
    field(["Python", "FastAPI"]);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
  });

  it("sends the whole list when one is added", async () => {
    const onChange = field(["Python"]);

    await userEvent.click(screen.getByRole("button", { name: "Stack" }));
    await userEvent.type(screen.getByLabelText("Stack"), "FastAPI");
    await userEvent.tab();

    expect(onChange).toHaveBeenCalledWith(["Python", "FastAPI"]);
  });

  it("sends the whole list when one is removed", async () => {
    const onChange = field(["Python", "FastAPI"]);

    await userEvent.click(screen.getByRole("button", { name: "Retirer Python" }));

    expect(onChange).toHaveBeenCalledWith(["FastAPI"]);
  });

  it("ignores an entry it already holds", async () => {
    const onChange = field(["Python"]);

    await userEvent.click(screen.getByRole("button", { name: "Stack" }));
    await userEvent.type(screen.getByLabelText("Stack"), "Python");
    await userEvent.tab();

    expect(onChange).not.toHaveBeenCalled();
  });

  describe("typing several in a row", () => {
    // The props do not come back between two entries: the server is slower
    // than the keyboard, and each entry must still reach it.
    it("keeps the first one when the second is typed before it is saved", async () => {
      const onChange = field([]);

      await userEvent.click(screen.getByRole("button", { name: "Stack" }));
      await userEvent.type(screen.getByLabelText("Stack"), "Python{Enter}");
      await userEvent.type(screen.getByLabelText("Stack"), "FastAPI{Enter}");

      expect(onChange).toHaveBeenNthCalledWith(1, ["Python"]);
      expect(onChange).toHaveBeenNthCalledWith(2, ["Python", "FastAPI"]);
    });

    it("shows both without waiting for the server", async () => {
      field([]);

      await userEvent.click(screen.getByRole("button", { name: "Stack" }));
      await userEvent.type(screen.getByLabelText("Stack"), "Python{Enter}");
      await userEvent.type(screen.getByLabelText("Stack"), "FastAPI{Enter}");

      expect(screen.getByText("Python")).toBeInTheDocument();
      expect(screen.getByText("FastAPI")).toBeInTheDocument();
    });

    it("removes one that the server has not confirmed yet", async () => {
      const onChange = field([]);

      await userEvent.click(screen.getByRole("button", { name: "Stack" }));
      await userEvent.type(screen.getByLabelText("Stack"), "Python{Enter}");
      await userEvent.keyboard("{Escape}");
      await userEvent.click(screen.getByRole("button", { name: "Retirer Python" }));

      expect(onChange).toHaveBeenLastCalledWith([]);
      expect(screen.queryByText("Python")).not.toBeInTheDocument();
    });
  });
});
