import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { UpdatesCounter } from "./UpdatesCounter";

const APERCU = <p>Le cadrage commence lundi</p>;

describe("UpdatesCounter", () => {
  it("shows nothing while the thread is empty", () => {
    const { container } = render(
      <UpdatesCounter count={0} preview={APERCU} onOpen={() => {}} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("counts the thread's updates", () => {
    render(<UpdatesCounter count={3} preview={APERCU} onOpen={() => {}} />);

    expect(screen.getByLabelText("3 mises à jour")).toHaveTextContent("3");
  });

  it("agrees the count in the singular", () => {
    render(<UpdatesCounter count={1} preview={APERCU} onOpen={() => {}} />);

    expect(screen.getByLabelText("1 mise à jour")).toBeInTheDocument();
  });

  it("shows the preview on hover", () => {
    render(<UpdatesCounter count={1} preview={APERCU} onOpen={() => {}} />);

    fireEvent.mouseMove(screen.getByLabelText("1 mise à jour"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Le cadrage commence lundi");
  });

  it("leads to the thread on click", () => {
    const open = vi.fn();
    render(<UpdatesCounter count={1} preview={APERCU} onOpen={open} />);

    fireEvent.click(screen.getByLabelText("1 mise à jour"));

    expect(open).toHaveBeenCalledTimes(1);
  });

  it("closes the tooltip when the mouse leaves the count", () => {
    render(<UpdatesCounter count={1} preview={APERCU} onOpen={() => {}} />);
    const counter = screen.getByLabelText("1 mise à jour");

    fireEvent.mouseMove(counter);
    fireEvent.mouseLeave(counter);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("counts without a tooltip when there is nothing to show", () => {
    render(<UpdatesCounter count={2} onOpen={() => {}} />);

    fireEvent.mouseMove(screen.getByLabelText("2 mises à jour"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
