import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MarkdownView } from "./MarkdownView";

describe("MarkdownView", () => {
  it("renders headings", () => {
    render(<MarkdownView body={"## Problème\n\nDu texte."} />);

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("Problème");
  });

  it("renders lists and code", () => {
    render(<MarkdownView body={"- import du CSV\n- via `WeasyPrint`"} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("WeasyPrint").tagName).toBe("CODE");
  });

  it("renders tables, which remark-gfm brings", () => {
    render(
      <MarkdownView body={"| Étape | Durée |\n| --- | --- |\n| Import | 2 s |"} />,
    );

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Étape" })).toBeInTheDocument();
  });

  it("ignores HTML rather than injecting it", () => {
    // Without `rehype-raw`, a tag written in the markdown stays text: nothing
    // is executed, so there is nothing to sanitise.
    const { container } = render(
      <MarkdownView body={'<img src=x onerror="alert(1)">Bonjour'} />,
    );

    expect(container.querySelector("img")).toBeNull();
    expect(container).toHaveTextContent("Bonjour");
  });

  it("keeps the links clickable", () => {
    render(<MarkdownView body="[La doc](https://waat.fr/doc)" />);

    expect(screen.getByRole("link", { name: "La doc" })).toHaveAttribute(
      "href",
      "https://waat.fr/doc",
    );
  });
});
