import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectAttachmentsTab } from "./ProjectAttachmentsTab";
import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";

const api = vi.hoisted(() => ({
  listProjectAttachments: vi.fn(),
  uploadProjectAttachment: vi.fn(),
  removeProjectAttachment: vi.fn(),
}));

vi.mock("@/lib/api/generated/projects/projects", () => api);

function file(
  changes: Partial<ProjectAttachmentResponse> = {},
): ProjectAttachmentResponse {
  return {
    id: 12,
    filename: "capture.png",
    content_type: "image/png",
    size_bytes: 2048,
    is_image: true,
    uploaded_at: "2026-05-20T11:35:00+00:00",
    uploader_name: "Alice Chen",
    used_in_updates: 0,
    ...changes,
  };
}

function served(files: ProjectAttachmentResponse[]) {
  api.listProjectAttachments.mockResolvedValue({ data: files });
}

beforeEach(() => {
  vi.clearAllMocks();
  served([]);
  api.uploadProjectAttachment.mockResolvedValue({ data: file() });
  api.removeProjectAttachment.mockResolvedValue({ data: null });
});

describe("ProjectAttachmentsTab", () => {
  it("says what to do when the project carries nothing yet", async () => {
    render(<ProjectAttachmentsTab projectId={7} />);

    expect(await screen.findByText(/Aucun fichier/)).toBeInTheDocument();
  });

  it("signs each file with who dropped it and when", async () => {
    served([file()]);

    render(<ProjectAttachmentsTab projectId={7} />);

    expect(
      await screen.findByText("Téléversé par Alice Chen le 20/05/2026 à 13h35"),
    ).toBeInTheDocument();
    expect(screen.getByText("capture.png")).toBeInTheDocument();
    expect(screen.getByText("2 ko")).toBeInTheDocument();
  });

  it("shows an image, and only names what is not one", async () => {
    served([
      file(),
      file({
        id: 13,
        filename: "note.pdf",
        content_type: "application/pdf",
        is_image: false,
      }),
    ]);

    render(<ProjectAttachmentsTab projectId={7} />);

    const shown = await screen.findAllByRole("img");
    expect(shown).toHaveLength(1);
    expect(shown[0]).toHaveAttribute(
      "src",
      "/api/v1/projects/7/attachments/12/content",
    );
    expect(screen.getByText("note.pdf")).toBeInTheDocument();
  });

  it("warns, before a file goes, about the thread that shows it", async () => {
    served([file({ used_in_updates: 2 })]);
    render(<ProjectAttachmentsTab projectId={7} />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Actions sur « capture.png »" }),
    );
    await userEvent.click(await screen.findByRole("button", { name: "Supprimer" }));

    expect(
      await screen.findByText(/affiché dans 2 mises à jour, qui montreront/),
    ).toBeInTheDocument();
  });

  it("withdraws the file once the question is answered", async () => {
    served([file()]);
    render(<ProjectAttachmentsTab projectId={7} />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Actions sur « capture.png »" }),
    );
    await userEvent.click(await screen.findByRole("button", { name: "Supprimer" }));
    await userEvent.click(
      await screen.findByRole("button", { name: "Supprimer le fichier" }),
    );

    await waitFor(() =>
      expect(api.removeProjectAttachment).toHaveBeenCalledWith(7, 12),
    );
  });

  it("opens a file in front of everything else", async () => {
    served([file()]);
    render(<ProjectAttachmentsTab projectId={7} />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Ouvrir « capture.png »" }),
    );

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("capture.png");
    expect(await screen.findByRole("link", { name: /Télécharger/ })).toHaveAttribute(
      "href",
      "/api/v1/projects/7/attachments/12/content?download=true",
    );
  });
});
