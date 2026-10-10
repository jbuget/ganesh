import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AdminPage } from "./AdminPage";

const view = vi.hoisted(() => ({ current: "plateforme" }));

vi.mock("@/lib/use-admin-view", () => ({
  useAdminView: () => ({ view: view.current, show: vi.fn() }),
}));
vi.mock("@/components/organisms/AdminPlatform", () => ({
  AdminPlatform: () => <p>La plateforme</p>,
}));
vi.mock("@/components/organisms/AssistantStudy", () => ({
  AssistantStudy: () => <p>L&apos;étude de l&apos;assistant</p>,
}));

describe("AdminPage", () => {
  it("opens on the platform", () => {
    view.current = "plateforme";
    render(<AdminPage />);

    expect(screen.getByRole("tab", { name: "Plateforme" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("La plateforme")).toBeInTheDocument();
  });

  it("reads the assistant on its own tab", () => {
    view.current = "assistant";
    render(<AdminPage />);

    expect(screen.getByRole("tab", { name: "Assistant IA" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("L'étude de l'assistant")).toBeInTheDocument();
  });
});
