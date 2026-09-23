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

  describe("when the list is long enough to be searched", () => {
    const PEOPLE = [
      { value: "1", label: "Lin Chen" },
      { value: "2", label: "Nino Garo" },
      { value: "3", label: "Éric Aubry" },
    ];

    function open(values: string[] = []) {
      const onChange = vi.fn();
      render(
        <FilterSelect
          label="Auteur"
          search="Rechercher un collaborateur"
          options={PEOPLE}
          values={values}
          onChange={onChange}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /Auteur/ }));
      return { onChange, field: screen.getByLabelText("Rechercher un collaborateur") };
    }

    it("offers no field where the caller asked for none", () => {
      render(
        <FilterSelect label="Phase" options={OPTIONS} values={[]} onChange={vi.fn()} />,
      );
      fireEvent.click(screen.getByRole("button", { name: /Phase/ }));

      expect(screen.queryByRole("searchbox")).toBeNull();
    });

    it("keeps only what is typed", () => {
      const { field } = open();

      fireEvent.change(field, { target: { value: "nino" } });

      expect(screen.getByRole("button", { name: "Nino Garo" })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Lin Chen" })).toBeNull();
    });

    /** Typing « eric » must find « Éric »: nobody types the accent to search. */
    it("ignores the case and the accents", () => {
      const { field } = open();

      fireEvent.change(field, { target: { value: "eric" } });

      expect(screen.getByRole("button", { name: "Éric Aubry" })).toBeInTheDocument();
    });

    it("still keeps a value on click once narrowed", () => {
      const { onChange, field } = open();

      fireEvent.change(field, { target: { value: "garo" } });
      fireEvent.click(screen.getByRole("button", { name: "Nino Garo" }));

      expect(onChange).toHaveBeenCalledWith(["2"]);
    });

    /** An empty panel reads as a bug; said, it reads as an answer. */
    it("says so when nothing answers", () => {
      const { field } = open();

      fireEvent.change(field, { target: { value: "zzz" } });

      expect(screen.getByText("Aucun résultat.")).toBeInTheDocument();
    });

    /**
     * What was kept stays kept: narrowing is a way of finding a value, not of
     * unticking the ones that scrolled out of sight.
     */
    it("leaves what is already kept alone", () => {
      const { onChange, field } = open(["1"]);

      fireEvent.change(field, { target: { value: "nino" } });
      fireEvent.click(screen.getByRole("button", { name: "Nino Garo" }));

      expect(onChange).toHaveBeenCalledWith(["1", "2"]);
    });
  });
});
