import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ReadOnlyBanner } from "./ReadOnlyBanner";

const mayWrite = vi.hoisted(() => ({ value: true }));
vi.mock("@/lib/use-may-write", () => ({ useMayWrite: () => mayWrite.value }));

describe("ReadOnlyBanner", () => {
  it("says nothing to somebody who may write", () => {
    mayWrite.value = true;
    const { container } = render(<ReadOnlyBanner />);

    expect(container).toBeEmptyDOMElement();
  });

  it("shows the band to a guest", () => {
    // What the band says is its own test: here it is only whether it is there.
    mayWrite.value = false;
    render(<ReadOnlyBanner />);

    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
