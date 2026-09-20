import { getDefaultNormalizer, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CopyableSnippet } from "@/components/atoms/CopyableSnippet";

const snippet = '{\n  "httpUrl": "https://api.ganesh.waat.tools/mcp/"\n}';

let writeText: ReturnType<typeof vi.fn>;

beforeEach(() => {
  writeText = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, { clipboard: { writeText } });
});

describe("CopyableSnippet", () => {
  it("shows the snippet whole, newlines included", () => {
    render(<CopyableSnippet value={snippet} label="Copier la configuration" />);
    // Not truncated: a configuration is read before it is pasted, and one cut
    // off at the edge of its box would be pasted wrong.
    expect(
      screen.getByText(snippet, {
        normalizer: getDefaultNormalizer({ collapseWhitespace: false }),
      }),
    ).toBeInTheDocument();
  });

  it("hands the whole thing over on a click", async () => {
    render(<CopyableSnippet value={snippet} label="Copier la configuration" />);

    await userEvent.click(
      screen.getByRole("button", { name: "Copier la configuration" }),
    );

    expect(writeText).toHaveBeenCalledWith(snippet);
  });

  it("says it copied, so the gesture is not made twice", async () => {
    render(<CopyableSnippet value={snippet} label="Copier la configuration" />);

    await userEvent.click(
      screen.getByRole("button", { name: "Copier la configuration" }),
    );

    expect(await screen.findByText("Copié")).toBeInTheDocument();
  });
});
