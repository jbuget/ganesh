import { describe, expect, it, vi } from "vitest";

import { awaitNewVersion } from "./await-new-version";

const instantly = () => Promise.resolve();

describe("awaitNewVersion", () => {
  it("hands back the version that appeared", async () => {
    const readLatest = vi.fn().mockResolvedValue(5);

    expect(await awaitNewVersion({ before: 4, readLatest, wait: instantly })).toBe(5);
  });

  it("keeps looking until one appears", async () => {
    const readLatest = vi
      .fn()
      .mockResolvedValueOnce(4)
      .mockResolvedValueOnce(4)
      .mockResolvedValueOnce(5);

    expect(await awaitNewVersion({ before: 4, readLatest, wait: instantly })).toBe(5);
    expect(readLatest).toHaveBeenCalledTimes(3);
  });

  it("gives up after the looks it was allowed", async () => {
    const readLatest = vi.fn().mockResolvedValue(4);

    const found = await awaitNewVersion({
      before: 4,
      readLatest,
      wait: instantly,
      polls: 3,
    });

    expect(found).toBeNull();
    expect(readLatest).toHaveBeenCalledTimes(3);
  });

  it("does not stop on a look that failed", async () => {
    const readLatest = vi
      .fn()
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValueOnce(5);

    expect(await awaitNewVersion({ before: 4, readLatest, wait: instantly })).toBe(5);
  });

  it("counts a first digest as an appearance", async () => {
    const readLatest = vi.fn().mockResolvedValue(1);

    expect(await awaitNewVersion({ before: 0, readLatest, wait: instantly })).toBe(1);
  });

  it("waits the delay it was given between looks", async () => {
    const wait = vi.fn().mockResolvedValue(undefined);

    await awaitNewVersion({
      before: 4,
      readLatest: () => Promise.resolve(4),
      wait,
      polls: 2,
      delayMs: 3000,
    });

    expect(wait).toHaveBeenCalledWith(3000);
    expect(wait).toHaveBeenCalledTimes(2);
  });
});
