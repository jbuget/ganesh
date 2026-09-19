import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodMark } from "./MoodMark";

describe("MoodMark", () => {
  it("names who posted it: the screen is nominative, and says so", () => {
    render(<MoodMark level="hard" initials="LC" />);

    expect(screen.getByText("LC")).toBeInTheDocument();
  });

  it("shows nothing for a level it does not know", () => {
    const { container } = render(
      // The API could one day carry a level this client has not been rebuilt
      // for: a missing mark reads better than a crash.
      <MoodMark level={"furious" as never} initials="LC" />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
