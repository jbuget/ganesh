import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReviewFlag } from "./ReviewFlag";

describe("ReviewFlag", () => {
  it("shows nothing when nothing is waiting", () => {
    const { container } = render(<ReviewFlag count={0} />);

    expect(container).toBeEmptyDOMElement();
  });

  /** À un, le drapeau le dit déjà : le nombre n'apporterait rien. */
  it("writes no number on a single line, and says so out loud", () => {
    render(<ReviewFlag count={1} />);

    expect(screen.getByLabelText("Une mise à jour à discuter")).toBeInTheDocument();
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });

  it("counts from two on", () => {
    render(<ReviewFlag count={3} />);

    expect(screen.getByLabelText("3 mises à jour à discuter")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("leads to the thread when it is given somewhere to lead", async () => {
    const onOpen = vi.fn();

    render(<ReviewFlag count={2} onOpen={onOpen} />);
    await userEvent.click(screen.getByRole("button"));

    expect(onOpen).toHaveBeenCalled();
  });

  /** La ligne entière ouvre déjà la mission : le clic ne doit pas y remonter. */
  it("keeps its click to itself", async () => {
    const rowClicked = vi.fn();

    render(
      // eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events
      <div onClick={rowClicked}>
        <ReviewFlag count={2} onOpen={vi.fn()} />
      </div>,
    );
    await userEvent.click(screen.getByRole("button"));

    expect(rowClicked).not.toHaveBeenCalled();
  });

  it("is not clickable when it leads nowhere", () => {
    render(<ReviewFlag count={2} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
