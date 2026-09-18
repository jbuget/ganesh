import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageLayout } from "./PageLayout";

describe("PageLayout", () => {
  it("shows the header and the content", () => {
    render(
      <PageLayout entete={<h1>Référentiel</h1>}>
        <p>Une mission</p>
      </PageLayout>,
    );

    expect(screen.getByRole("heading", { name: "Référentiel" })).toBeInTheDocument();
    expect(screen.getByText("Une mission")).toBeInTheDocument();
  });

  it("keeps the header out of the scrolling area", () => {
    // That is the whole point of the skeleton: were the header to share the
    // scrolling container, it would go off with the content.
    render(
      <PageLayout entete={<h1>Référentiel</h1>}>
        <p>Une mission</p>
      </PageLayout>,
    );

    const defilante = screen.getByText("Une mission").closest(".overflow-y-auto");

    expect(defilante).not.toBeNull();
    expect(defilante).not.toContainElement(screen.getByRole("heading"));
  });
});
