import { describe, expect, it } from "vitest";

import {
  contentUrl,
  downloadUrl,
  formatBytes,
  isRenderableImage,
  shownInUpdates,
  uploadedBy,
} from "@/lib/attachments";

describe("where a file is read from", () => {
  it("is a relative address, so it goes through the BFF", () => {
    expect(contentUrl(4, 12)).toBe("/api/v1/projects/4/attachments/12/content");
  });

  it("asks to be offered rather than shown when one comes to save it", () => {
    expect(downloadUrl(4, 12)).toBe(
      "/api/v1/projects/4/attachments/12/content?download=true",
    );
  });
});

describe("a size, as one says it", () => {
  it("counts bytes while there are few", () => {
    expect(formatBytes(512)).toBe("512 o");
  });

  it("turns to kilobytes of 1024", () => {
    expect(formatBytes(2048)).toBe("2 ko");
  });

  it("keeps one decimal where it says something", () => {
    expect(formatBytes(1_468_006)).toBe("1,4 Mo");
  });

  it("drops the decimal where it says nothing", () => {
    expect(formatBytes(12 * 1024 * 1024)).toBe("12 Mo");
  });

  it("writes a decimal with a comma, as French does", () => {
    expect(formatBytes(1536)).toBe("1,5 ko");
  });

  it("never climbs past megabytes: nothing here weighs more", () => {
    expect(formatBytes(10 * 1024 * 1024)).toBe("10 Mo");
  });
});

describe("the signature of a file", () => {
  it("says who dropped it and when", () => {
    expect(uploadedBy("Alice Chen", "2026-05-20T11:35:00+00:00")).toBe(
      "Téléversé par Alice Chen le 20/05/2026 à 13h35",
    );
  });
});

describe("what a thread would lose", () => {
  it("says nothing when no update shows the file", () => {
    expect(shownInUpdates(0)).toBeNull();
  });

  it("stays singular for one", () => {
    expect(shownInUpdates(1)).toContain("une mise à jour, qui montrera");
  });

  it("agrees in the plural", () => {
    expect(shownInUpdates(3)).toContain("3 mises à jour, qui montreront");
  });
});

describe("isRenderableImage", () => {
  it("draws a photograph", () => {
    expect(isRenderableImage("image/png")).toBe(true);
    expect(isRenderableImage("image/jpeg")).toBe(true);
  });

  it("never draws a drawing that runs scripts", () => {
    // The API refuses to serve it inline: an <img> would never load.
    expect(isRenderableImage("image/svg+xml")).toBe(false);
  });

  it("reads the type whatever it was dressed in", () => {
    expect(isRenderableImage("IMAGE/PNG; charset=binary")).toBe(true);
  });

  it("draws nothing of what is not an image", () => {
    expect(isRenderableImage("application/pdf")).toBe(false);
    expect(isRenderableImage("text/html")).toBe(false);
  });
});
