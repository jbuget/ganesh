import { describe, expect, it } from "vitest";

import { once } from "./single-flight";

/** A task that only finishes when told to, and counts how often it started. */
function heldTask() {
  let release: (value: string) => void = () => {};
  const held = new Promise<string>((resolve) => {
    release = resolve;
  });
  let starts = 0;
  return {
    starts: () => starts,
    release,
    start: () => {
      starts += 1;
      return held;
    },
  };
}

describe("one piece of work at a time", () => {
  it("runs the work once for everyone asking at the same time", async () => {
    const task = heldTask();

    const [first, second] = [once("k", task.start), once("k", task.start)];
    task.release("done");

    expect(await first).toBe("done");
    expect(await second).toBe("done");
    expect(task.starts()).toBe(1);
  });

  it("keeps two keys apart", async () => {
    const task = heldTask();

    void once("a", task.start);
    void once("b", task.start);
    task.release("done");

    expect(task.starts()).toBe(2);
  });

  it("starts afresh once the first has finished", async () => {
    const task = heldTask();

    const first = once("k", task.start);
    task.release("done");
    await first;
    void once("k", task.start);

    expect(task.starts()).toBe(2);
  });

  /** A failure held on to would leave every later attempt waiting for nothing. */
  it("starts afresh after a failure", async () => {
    let starts = 0;
    const failing = () => {
      starts += 1;
      return Promise.reject(new Error("nope"));
    };

    await expect(once("k", failing)).rejects.toThrow("nope");
    await expect(once("k", failing)).rejects.toThrow("nope");

    expect(starts).toBe(2);
  });
});
