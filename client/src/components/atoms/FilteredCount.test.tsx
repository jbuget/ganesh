import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { FilteredCount } from "./FilteredCount";

describe("FilteredCount", () => {
  it("says what is seen against what could be seen", () => {
    render(<FilteredCount visible={3} total={12} one="projet" many="projets" />);

    expect(screen.getByRole("status")).toHaveTextContent("3 projets sur 12");
  });

  it("agrees the noun with what is counted", () => {
    // « 1 projets sur 12 » is read as a typo, and a typo is read as a bug.
    render(<FilteredCount visible={1} total={12} one="projet" many="projets" />);

    expect(screen.getByRole("status")).toHaveTextContent("1 projet sur 12");
  });

  it("speaks a filter that leaves nothing aloud", () => {
    render(
      <FilteredCount
        visible={0}
        total={12}
        one="collaborateur"
        many="collaborateurs"
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("0 collaborateur sur 12");
  });
});
