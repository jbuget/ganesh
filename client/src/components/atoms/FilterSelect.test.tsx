import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { FilterSelect } from "./FilterSelect";

const OPTIONS = [
  { value: "scoping", label: "Cadrage" },
  { value: "development", label: "Réalisation" },
];

describe("FilterSelect", () => {
  it("announces the criterion when nothing is kept", () => {
    render(
      <FilterSelect label="Phase" options={OPTIONS} values={[]} onChange={vi.fn()} />,
    );

    expect(screen.getByRole("button", { name: /Phase/ })).toBeInTheDocument();
  });

  it("counts the values kept on the trigger", () => {
    render(
      <FilterSelect
        label="Phase"
        options={OPTIONS}
        values={["scoping", "development"]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /Phase/ })).toHaveTextContent("2");
  });

  it("adds a value on click", () => {
    const onChange = vi.fn();
    render(
      <FilterSelect label="Phase" options={OPTIONS} values={[]} onChange={onChange} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadrage" }));

    expect(onChange).toHaveBeenCalledWith(["scoping"]);
  });

  it("removes a value already kept", () => {
    const onChange = vi.fn();
    render(
      <FilterSelect
        label="Phase"
        options={OPTIONS}
        values={["scoping"]}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadrage" }));

    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("returns the values in the order of the options, whatever the order of the clicks", () => {
    const onChange = vi.fn();
    render(
      <FilterSelect
        label="Phase"
        options={OPTIONS}
        values={["development"]}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadrage" }));

    expect(onChange).toHaveBeenCalledWith(["scoping", "development"]);
  });
});
