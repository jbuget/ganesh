import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MoodReminder } from "./MoodReminder";
import { STRONG_RULE } from "@/lib/table-frame";

const reminder = vi.hoisted(() => ({
  show: true,
  saving: false,
  post: vi.fn(),
  dismiss: vi.fn(),
}));

vi.mock("@/lib/use-mood-reminder", () => ({ useMoodReminder: () => reminder }));

beforeEach(() => {
  vi.clearAllMocks();
  reminder.show = true;
  reminder.saving = false;
});

describe("MoodReminder", () => {
  it("shows nothing at all when there is nothing to ask", () => {
    reminder.show = false;

    const { container } = render(<MoodReminder />);

    expect(container).toBeEmptyDOMElement();
  });

  it("asks the day, and says who reads the answer", () => {
    render(<MoodReminder />);

    expect(
      screen.getByRole("heading", { name: /Comment s'est passée votre journée/ }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Toute l'équipe lit le résultat/)).toBeInTheDocument();
  });

  it("posts the face one picks", () => {
    render(<MoodReminder />);

    fireEvent.click(screen.getByRole("radio", { name: "Bonne" }));

    expect(reminder.post).toHaveBeenCalledWith("good");
  });

  it("offers the five faces on a day nobody has answered for", () => {
    render(<MoodReminder />);

    const faces = screen.getAllByRole("radio");
    expect(faces).toHaveLength(5);
    expect(faces.every((face) => face.getAttribute("aria-checked") === "false")).toBe(
      true,
    );
  });

  it("holds the faces while the answer travels", () => {
    reminder.saving = true;

    render(<MoodReminder />);

    expect(screen.getByRole("radio", { name: "Bonne" })).toBeDisabled();
  });

  it("is turned down in one click", () => {
    render(<MoodReminder />);

    fireEvent.click(screen.getByRole("button", { name: "Pas aujourd'hui" }));

    expect(reminder.dismiss).toHaveBeenCalled();
  });
});

describe("how it sits on the page", () => {
  it("is announced, rather than slipped into a corner nobody watches", () => {
    render(<MoodReminder />);

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("closes at the weight the application closes an object at", () => {
    render(<MoodReminder />);

    expect(screen.getByRole("status").className).toContain(STRONG_RULE);
  });

  it("stays under the panels one opens oneself", () => {
    // It arrives on its own; a side panel is a gesture, and comes first.
    render(<MoodReminder />);

    expect(screen.getByRole("status").className).toContain("z-30");
  });
});
