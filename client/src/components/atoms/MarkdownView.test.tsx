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

  it("shows an image written in the markdown", () => {
    // What a capture pasted into an update becomes: an ordinary markdown
    // image, pointing at the address the BFF serves the file from.
    render(
      <MarkdownView body="![capture](/api/v1/projects/4/attachments/12/content)" />,
    );

    expect(screen.getByRole("img", { name: "capture" })).toHaveAttribute(
      "src",
      "/api/v1/projects/4/attachments/12/content",
    );
  });

  it("keeps the links clickable", () => {
    render(<MarkdownView body="[La doc](https://waat.fr/doc)" />);

    expect(screen.getByRole("link", { name: "La doc" })).toHaveAttribute(
      "href",
      "https://waat.fr/doc",
    );
  });

  it("draws its links the way it is told to", () => {
    render(
      <MarkdownView
        body={"Voir [EDIT](/projects/85)."}
        renderLink={(href, children) => <mark data-href={href}>{children}</mark>}
      />,
    );

    expect(screen.getByText("EDIT").tagName).toBe("MARK");
    expect(screen.getByText("EDIT")).toHaveAttribute("data-href", "/projects/85");
  });

  it("draws no image when asked not to", () => {
    const { container } = render(
      <MarkdownView
        body={"Voir ![x](https://ailleurs.example/?q=secret)."}
        images={false}
      />,
    );

    expect(container.querySelector("img")).toBeNull();
  });

  it("hands the tree to the plugins it is given", () => {
    const shout =
      () => (tree: { children?: { children?: { value?: string }[] }[] }) => {
        const text = tree.children?.[0]?.children?.[0];
        if (text) text.value = "TOUT FORT";
      };
    render(<MarkdownView body="tout bas" plugins={[shout]} />);

    expect(screen.getByText("TOUT FORT")).toBeInTheDocument();
  });
});
