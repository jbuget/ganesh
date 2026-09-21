import { describe, expect, it } from "vitest";

import { imagesIn } from "@/lib/pasted-images";

/** A `DataTransfer` as the browser hands one over, jsdom having none. */
function carrying(files: File[]): DataTransfer {
  return { files, types: files.length ? ["Files"] : [] } as unknown as DataTransfer;
}

const CAPTURE = new File(["x"], "capture.png", { type: "image/png" });
const NOTE = new File(["x"], "note.pdf", { type: "application/pdf" });

describe("what an editor takes out of a paste", () => {
  it("takes nothing when there is nothing to take", () => {
    expect(imagesIn(null)).toEqual([]);
    expect(imagesIn(carrying([]))).toEqual([]);
  });

  it("takes a pasted capture", () => {
    expect(imagesIn(carrying([CAPTURE]))).toEqual([CAPTURE]);
  });

  it("leaves what is not an image to the editor", () => {
    expect(imagesIn(carrying([NOTE]))).toEqual([]);
  });

  it("keeps the order several images came in", () => {
    const second = new File(["x"], "autre.jpg", { type: "image/jpeg" });

    expect(imagesIn(carrying([CAPTURE, NOTE, second]))).toEqual([CAPTURE, second]);
  });
});
