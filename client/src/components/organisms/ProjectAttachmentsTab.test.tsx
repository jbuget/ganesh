import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectAttachmentsTab } from "./ProjectAttachmentsTab";
import type { ProjectAttachmentResponse } from "@/lib/api/generated/model";

const api = vi.hoisted(() => ({
  listProjectAttachments: vi.fn(),
  uploadProjectAttachment: vi.fn(),
  renameProjectAttachment: vi.fn(),
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
  api.renameProjectAttachment.mockResolvedValue({ data: file() });
  api.removeProjectAttachment.mockResolvedValue({ data: null });
});

describe("ProjectAttachmentsTab", () => {
  it("says what to do when the project carries nothing yet", async () => {
    render(<ProjectAttachmentsTab projectId={7} />);

    expect(await screen.findByText(/Aucun fichier/)).toBeInTheDocument();
  });

  it("reads a file by its name and its weight", async () => {
    served([file()]);

    render(<ProjectAttachmentsTab projectId={7} />);

    expect(await screen.findByText("capture.png")).toBeInTheDocument();
    expect(screen.getByText("2 ko")).toBeInTheDocument();
    // The signature is not read first: it waits under the corner mark.
    expect(
      screen.queryByText("Téléversé par Alice Chen le 20/05/2026 à 13h35"),
    ).not.toBeInTheDocument();
  });

  it("says who dropped the file, and when, to whoever asks the corner mark", async () => {
    served([file()]);
    render(<ProjectAttachmentsTab projectId={7} />);
    const said = "Téléversé par Alice Chen le 20/05/2026 à 13h35";

    await userEvent.hover(await screen.findByLabelText(said));

    // The label is what a screen reader hears; this is what an eye reads.
    expect(await screen.findByText(said)).toBeVisible();
  });

  it("offers the gestures on the file itself", async () => {
    served([file()]);
    render(<ProjectAttachmentsTab projectId={7} />);

    // Opening has its own control; the rest waits behind the menu.
    expect(
      await screen.findByRole("button", { name: "Ouvrir « capture.png »" }),
    ).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur « capture.png »" }),
    );
    expect(await screen.findByRole("button", { name: "Renommer" })).toBeInTheDocument();
  });

  it("renames a file, and keeps the link the thread already cites", async () => {
    served([file()]);
    render(<ProjectAttachmentsTab projectId={7} />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Actions sur « capture.png »" }),
    );
    await userEvent.click(await screen.findByRole("button", { name: "Renommer" }));
    const field = await screen.findByLabelText("Nom du fichier");
    await userEvent.clear(field);
    await userEvent.type(field, "bug de mars.png");
    await userEvent.click(screen.getByRole("button", { name: "Renommer" }));

    await waitFor(() =>
      expect(api.renameProjectAttachment).toHaveBeenCalledWith(7, 12, {
        filename: "bug de mars.png",
      }),
    );
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

  it("offers a file to save as a link, never as a jump", () => {
    served([file()]);
    render(<ProjectAttachmentsTab projectId={7} />);

    return screen
      .findByRole("button", { name: "Actions sur « capture.png »" })
      .then(async (menu) => {
        await userEvent.click(menu);
        const link = await screen.findByRole("link", { name: /Télécharger/ });
        expect(link).toHaveAttribute(
          "href",
          "/api/v1/projects/7/attachments/12/content?download=true",
        );
        expect(link).toHaveAttribute("download", "capture.png");
      });
  });

  it("lands the files a single drop carried, one refusal aside", async () => {
    api.uploadProjectAttachment
      .mockRejectedValueOnce(new Error("refusé"))
      .mockResolvedValue({ data: file() });
    render(<ProjectAttachmentsTab projectId={7} />);
    const picker = document.querySelector("input[type=file]") as HTMLInputElement;

    await userEvent.upload(picker, [
      new File(["a"], "un.png", { type: "image/png" }),
      new File(["b"], "deux.png", { type: "image/png" }),
    ]);

    // The second one still went up: a refusal does not take the drop with it.
    await waitFor(() => expect(api.uploadProjectAttachment).toHaveBeenCalledTimes(2));
  });
});
