import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ReadOnlyNotice } from "./ReadOnlyNotice";

describe("ReadOnlyNotice", () => {
  it("says what the account does, and who opens it up", () => {
    render(<ReadOnlyNotice />);

    expect(screen.getByRole("status")).toHaveTextContent(/lit Ganesh sans y écrire/);
    // « refusé » with no way forward is a dead end: the band names who hands
    // the rights out.
    expect(screen.getByRole("status")).toHaveTextContent(/manager/);
  });
});
