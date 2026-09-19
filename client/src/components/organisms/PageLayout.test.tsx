import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageLayout } from "./PageLayout";

describe("PageLayout", () => {
  it("shows the header and the content", () => {
    render(
      <PageLayout header={<h1>Référentiel</h1>}>
        <p>Un projet</p>
      </PageLayout>,
    );

    expect(screen.getByRole("heading", { name: "Référentiel" })).toBeInTheDocument();
    expect(screen.getByText("Un projet")).toBeInTheDocument();
  });

  it("keeps the header out of the scrolling area", () => {
    // That is the whole point of the skeleton: were the header to share the
    // scrolling container, it would go off with the content.
    render(
      <PageLayout header={<h1>Référentiel</h1>}>
        <p>Un projet</p>
      </PageLayout>,
    );

    const scroller = screen.getByText("Un projet").closest(".overflow-y-auto");

    expect(scroller).not.toBeNull();
    expect(scroller).not.toContainElement(screen.getByRole("heading"));
  });
});
