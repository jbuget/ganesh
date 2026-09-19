import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import type { ProjectLinkResponse } from "@/lib/api/generated/model";

import { ProjectLinks } from "./ProjectLinks";

const link = (over: Partial<ProjectLinkResponse> = {}): ProjectLinkResponse => ({
  id: 1,
  label: "Le dépôt",
  url: "https://github.com/waat/portail",
  icon: "repository",
  ...over,
});

describe("ProjectLinks", () => {
  it("opens the address in another tab", () => {
    render(<ProjectLinks links={[link()]} />);

    const anchor = screen.getByRole("link", { name: /Le dépôt/ });
    expect(anchor).toHaveAttribute("href", "https://github.com/waat/portail");
    expect(anchor).toHaveAttribute("target", "_blank");
  });

  it("names the link and its family, which the icon alone does not say", () => {
    render(<ProjectLinks links={[link()]} />);

    expect(
      screen.getByRole("link", { name: "Le dépôt (Dépôt de code)" }),
    ).toBeInTheDocument();
  });

  it("does not open the row underneath", () => {
    const onRowClick = vi.fn();
    render(
      <div onClick={onRowClick}>
        <ProjectLinks links={[link()]} />
      </div>,
    );

    fireEvent.click(screen.getByRole("link", { name: /Le dépôt/ }));

    expect(onRowClick).not.toHaveBeenCalled();
  });

  it("counts the ones it cannot show rather than overflowing", () => {
    render(
      <ProjectLinks
        links={[
          link({ id: 1, label: "Un" }),
          link({ id: 2, label: "Deux" }),
          link({ id: 3, label: "Trois" }),
          link({ id: 4, label: "Quatre" }),
          link({ id: 5, label: "Cinq" }),
        ]}
      />,
    );

    expect(screen.getAllByRole("link")).toHaveLength(3);
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("draws nothing without a link", () => {
    const { container } = render(<ProjectLinks links={[]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
