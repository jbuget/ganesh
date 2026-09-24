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

  it("tells a guest what their account does, and who opens it up", () => {
    mayWrite.value = false;
    render(<ReadOnlyBanner />);

    expect(screen.getByRole("status")).toHaveTextContent(/lit Ganesh sans y écrire/);
    // « refusé » with no way forward is a dead end: the band names who hands
    // the rights out.
    expect(screen.getByRole("status")).toHaveTextContent(/manager/);
  });
});
