import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MessageCircle } from "lucide-react";

import { CardCounter } from "./CardCounter";

const PREVIEW = <p>Le cadrage commence lundi</p>;

const counter = (count: number, preview?: React.ReactNode, onOpen?: () => void) => (
  <CardCounter
    icon={MessageCircle}
    count={count}
    label={["commentaire", "commentaires"]}
    empty="Aucun commentaire"
    preview={preview}
    onOpen={onOpen}
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
    const count = screen.getByLabelText("2 commentaires");

    fireEvent.mouseMove(count);
    fireEvent.mouseLeave(count);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("counts without a tooltip when there is nothing to show", () => {
    render(counter(2));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  describe("quand le compte mène quelque part", () => {
    it("counts nothing clickable when it leads nowhere", () => {
      render(counter(2));

      expect(screen.queryByRole("button")).not.toBeInTheDocument();
    });

    it("opens what it counts", async () => {
      const onOpen = vi.fn();
      render(counter(2, undefined, onOpen));

      await userEvent.click(screen.getByRole("button", { name: "2 commentaires" }));

      expect(onOpen).toHaveBeenCalledTimes(1);
    });

    it("opens it at zero too: one writes the first message from there", async () => {
      const onOpen = vi.fn();
      render(counter(0, undefined, onOpen));

      await userEvent.click(screen.getByRole("button", { name: "Aucun commentaire" }));

      expect(onOpen).toHaveBeenCalledTimes(1);
    });

    it("leaves the card it sits on alone", async () => {
      // The whole card opens the mission: without stopping propagation, the
      // click would open it twice, the second time on the wrong tab.
      const onCard = vi.fn();
      const onOpen = vi.fn();
      render(<div onClick={onCard}>{counter(2, undefined, onOpen)}</div>);

      await userEvent.click(screen.getByRole("button", { name: "2 commentaires" }));

      expect(onOpen).toHaveBeenCalledTimes(1);
      expect(onCard).not.toHaveBeenCalled();
    });

    it("still shows the preview on hover", () => {
      render(counter(2, PREVIEW, vi.fn()));

      fireEvent.mouseMove(screen.getByRole("button", { name: "2 commentaires" }));

      expect(screen.getByRole("tooltip")).toHaveTextContent(
        "Le cadrage commence lundi",
      );
    });
  });
});
