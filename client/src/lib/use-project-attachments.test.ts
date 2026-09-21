import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useProjectAttachments } from "./use-project-attachments";

const api = vi.hoisted(() => ({
  listProjectAttachments: vi.fn(),
  uploadProjectAttachment: vi.fn(),
  removeProjectAttachment: vi.fn(),
}));

vi.mock("@/lib/api/generated/projects/projects", () => api);

function aFile(name = "capture.png", size = 2048): File {
  const file = new File(["x"], name, { type: "image/png" });
  Object.defineProperty(file, "size", { value: size });
  return file;
}

beforeEach(() => {
  vi.clearAllMocks();
  api.listProjectAttachments.mockResolvedValue({ data: [] });
  api.uploadProjectAttachment.mockResolvedValue({ data: { id: 12 } });
  api.removeProjectAttachment.mockResolvedValue({ data: null });
});

async function tab(onWrite?: () => void | Promise<void>) {
  const { result } = renderHook(() => useProjectAttachments(7, onWrite));
  await waitFor(() => expect(result.current.files).not.toBeNull());
  return result;
}

describe("useProjectAttachments", () => {
  it("hands back the address the file is now served at", async () => {
    const result = await tab();

    let url = "";
    await act(async () => {
      url = await result.current.upload(aFile());
    });

    expect(api.uploadProjectAttachment).toHaveBeenCalledWith(7, {
      file: expect.any(File),
    });
    expect(url).toBe("/api/v1/projects/7/attachments/12/content");
  });

  it("reads the list back after a drop, and tells the screen one came from", async () => {
    const notify = vi.fn();
    const result = await tab(notify);

    await act(async () => {
      await result.current.upload(aFile());
    });

    expect(api.listProjectAttachments).toHaveBeenCalledTimes(2);
    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("refuses a file over ten megabytes without sending it", async () => {
    const result = await tab();

    await act(async () => {
      await expect(
        result.current.upload(aFile("gros.zip", 11 * 1024 * 1024)),
      ).rejects.toThrow();
    });

    expect(api.uploadProjectAttachment).not.toHaveBeenCalled();
    expect(result.current.error).toContain("gros.zip");
  });

  it("reads the list back after a withdrawal too", async () => {
    const notify = vi.fn();
    const result = await tab(notify);

    await act(async () => {
      await result.current.remove(12);
    });

    expect(api.removeProjectAttachment).toHaveBeenCalledWith(7, 12);
    expect(api.listProjectAttachments).toHaveBeenCalledTimes(2);
    expect(notify).toHaveBeenCalledTimes(1);
  });
});
