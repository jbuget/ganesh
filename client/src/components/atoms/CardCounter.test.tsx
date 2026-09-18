import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MessageCircle } from "lucide-react";

import { CardCounter } from "./CardCounter";

const PREVIEW = <p>Le cadrage commence lundi</p>;

const counter = (count: number, preview?: React.ReactNode) => (
  <CardCounter
    icon={MessageCircle}
    count={count}
    label={["commentaire", "commentaires"]}
    empty="Aucun commentaire"
    preview={preview}
  />
);

describe("CardCounter", () => {
  it("announces the number in the plural", () => {
    render(counter(3));

    expect(screen.getByLabelText("3 commentaires")).toHaveTextContent("3");
  });

  it("agrees in the singular", () => {
    render(counter(1));

    expect(screen.getByLabelText("1 commentaire")).toBeInTheDocument();
  });

  it("keeps the icon without a number when there is nothing to count", () => {
    render(counter(0));

    expect(screen.getByLabelText("Aucun commentaire")).toHaveTextContent("");
  });

  it("dims the icon when the count is nil", () => {
    render(counter(0));

    expect(screen.getByLabelText("Aucun commentaire").className).toContain(
      "text-slate-300",
    );
  });

  it("shows the preview on hover", () => {
    render(counter(2, PREVIEW));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Le cadrage commence lundi");
  });

  it("closes the preview when the mouse leaves the count", () => {
    render(counter(2, PREVIEW));
    const decompte = screen.getByLabelText("2 commentaires");

    fireEvent.mouseMove(decompte);
    fireEvent.mouseLeave(decompte);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("counts without a tooltip when there is nothing to show", () => {
    render(counter(2));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
