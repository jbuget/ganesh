import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AdminPage } from "./AdminPage";

const platform = vi.hoisted(() => ({
  state: {
    isLoading: false,
    platform: {
      environment: "production",
      door: "ENTRA",
      services: [
        { name: "entra", configured: true, detail: "tenant-1" },
        { name: "gemini", configured: false, detail: "" },
        { name: "smtp", configured: true, detail: "smtp.mailgun.org:587" },
        { name: "s3", configured: true, detail: "ganesh-attachments" },
      ],
    },
  } as Record<string, unknown>,
}));

vi.mock("@/lib/api/queries", () => ({ usePlatform: () => platform.state }));

describe("AdminPage", () => {
  it("says which door signs people in", () => {
    render(<AdminPage />);

    expect(screen.getByText(/Microsoft Entra ID —/)).toBeInTheDocument();
  });

  it("tells a service that is wired from one that is not", () => {
    render(<AdminPage />);

    expect(screen.getAllByText("Câblé").length).toBe(3);
    expect(screen.getByText("Non câblé")).toBeInTheDocument();
  });

  it("says what a missing service costs rather than leaving it at a fault", () => {
    render(<AdminPage />);

    expect(screen.getByText(/sans chapeau/)).toBeInTheDocument();
  });

  it("offers nothing to change: the platform is read here, not steered", () => {
    render(<AdminPage />);

    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
  });

  it("says where the roles are handed out rather than handing them out", () => {
    render(<AdminPage />);

    expect(screen.getByText(/écran « Utilisateurs »/)).toBeInTheDocument();
  });
});
