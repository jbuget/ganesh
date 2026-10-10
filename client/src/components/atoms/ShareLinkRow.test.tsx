import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ShareLinkRow } from "./ShareLinkRow";

function aRow(over: Partial<React.ComponentProps<typeof ShareLinkRow>> = {}) {
  const props = {
    address: "https://ganesh.waat.tools/p/gazette/abc",
    openedBy: "Ouvert par Léa Chen le 11 octobre 2026",
    onCopy: vi.fn(),
    onClose: vi.fn(),
    ...over,
  };
  render(<ShareLinkRow {...props} />);
  return props;
}

describe("ShareLinkRow", () => {
  it("shows the address in full, to be selected and pasted", () => {
    aRow();

    expect(screen.getByLabelText("Adresse du lien")).toHaveValue(
      "https://ganesh.waat.tools/p/gazette/abc",
    );
  });

  it("says who opened it and when", () => {
    aRow();

    expect(screen.getByText(/Ouvert par Léa Chen/)).toBeVisible();
  });

  it("copies the link and says it did", async () => {
    const props = aRow();

    await userEvent.click(screen.getByRole("button", { name: "Copier le lien" }));

    expect(props.onCopy).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Lien copié" })).toBeVisible();
  });

  it("closes the link", async () => {
    const props = aRow();

    await userEvent.click(screen.getByRole("button", { name: "Fermer le lien" }));

    expect(props.onClose).toHaveBeenCalledTimes(1);
  });
});
