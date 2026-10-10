import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { NameLink } from "./NameLink";

describe("NameLink", () => {
  it("draws a project as a link to its sheet", () => {
    render(<NameLink href="/projects/85">EDIT</NameLink>);

    const link = screen.getByRole("link", { name: "EDIT" });
    expect(link).toHaveAttribute("href", "/projects/85");
    expect(link).toHaveClass("text-sky-700");
  });

  it("draws a person in strong type, leading to their panel", () => {
    render(<NameLink href="/users?user=3">David DEHE</NameLink>);

    const link = screen.getByRole("link", { name: "David DEHE" });
    expect(link).toHaveAttribute("href", "/users?user=3");
    expect(link).toHaveClass("font-semibold", "text-slate-900!");
  });

  it("draws any other address as words, never as a link", () => {
    render(<NameLink href="https://ailleurs.example/?q=secret">la doc</NameLink>);

    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByText("la doc")).toBeInTheDocument();
  });
});
