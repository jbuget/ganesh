import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { FilterSelect } from "./FilterSelect";

const OPTIONS = [
  { valeur: "cadrage", libelle: "Cadrage" },
  { valeur: "realisation", libelle: "Réalisation" },
];

describe("FilterSelect", () => {
  it("annonce le critère quand rien n'est retenu", () => {
    render(
      <FilterSelect
        libelle="Phase"
        options={OPTIONS}
        valeurs={[]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /Phase/ })).toBeInTheDocument();
  });

  it("compte les valeurs retenues sur le déclencheur", () => {
    render(
      <FilterSelect
        libelle="Phase"
        options={OPTIONS}
        valeurs={["cadrage", "realisation"]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /Phase/ })).toHaveTextContent("2");
  });

  it("ajoute une valeur au clic", () => {
    const onChange = vi.fn();
    render(
      <FilterSelect
        libelle="Phase"
        options={OPTIONS}
        valeurs={[]}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadrage" }));

    expect(onChange).toHaveBeenCalledWith(["cadrage"]);
  });

  it("retire une valeur déjà retenue", () => {
    const onChange = vi.fn();
    render(
      <FilterSelect
        libelle="Phase"
        options={OPTIONS}
        valeurs={["cadrage"]}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadrage" }));

    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("rend les valeurs dans l'ordre des options, quel que soit l'ordre des clics", () => {
    const onChange = vi.fn();
    render(
      <FilterSelect
        libelle="Phase"
        options={OPTIONS}
        valeurs={["realisation"]}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadrage" }));

    expect(onChange).toHaveBeenCalledWith(["cadrage", "realisation"]);
  });
});
