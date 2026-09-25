import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RequestStateMark } from "./RequestStateMark";

describe("RequestStateMark", () => {
  it("says where the need stands, in French", () => {
    render(<RequestStateMark value="deferred" />);

    expect(screen.getByText("Plus tard")).toBeInTheDocument();
  });
});
