import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PresenceMark } from "@/components/atoms/PresenceMark";

describe("where somebody is, as a mark", () => {
  it("names the place for whoever cannot see the mark", () => {
    render(<PresenceMark day="REMOTE" />);

    expect(screen.getByRole("img", { name: "télétravail" })).toBeInTheDocument();
  });

  it("tells the three apart by shape, not by colour alone", () => {
    // Filled on site, hollow at home, dotted for a day away: read the same by
    // whoever cannot tell the colours, and legible down to 13 px.
    const { container: onSite } = render(<PresenceMark day="ON_SITE" />);
    const { container: remote } = render(<PresenceMark day="REMOTE" />);
    const { container: away } = render(<PresenceMark day="AWAY" />);

    expect(onSite.firstElementChild?.className).toContain("bg-sky-600");
    expect(remote.firstElementChild?.className).not.toContain("bg-sky-600");
    expect(away.firstElementChild?.className).toContain("border-dotted");
  });

  it("steps aside where the cell around it already says the day", () => {
    // Announced twice, a mark makes a screen reader read every row twice.
    render(<PresenceMark day="ON_SITE" labelled={false} />);

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
