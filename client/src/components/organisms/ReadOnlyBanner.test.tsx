import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ReadOnlyBanner } from "./ReadOnlyBanner";

const mayWrite = vi.hoisted(() => ({ value: true }));
const borrowing = vi.hoisted(() => ({ value: false }));
vi.mock("@/lib/use-may-write", () => ({
  useMayWrite: () => mayWrite.value,
  useIsBorrowing: () => borrowing.value,
}));

describe("ReadOnlyBanner", () => {
  it("says nothing to somebody who may write", () => {
    mayWrite.value = true;
    borrowing.value = false;
    const { container } = render(<ReadOnlyBanner />);

    expect(container).toBeEmptyDOMElement();
  });

  it("shows the band to a guest", () => {
    // What the band says is its own test: here it is only whether it is there.
    mayWrite.value = false;
    borrowing.value = false;
    render(<ReadOnlyBanner />);

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("stands down while an account is being borrowed", () => {
    // The borrowing band above says the same thing, and says whose account it
    // is. Two bands stacked teach the reader to look past both.
    mayWrite.value = false;
    borrowing.value = true;
    const { container } = render(<ReadOnlyBanner />);

    expect(container).toBeEmptyDOMElement();
  });
});
