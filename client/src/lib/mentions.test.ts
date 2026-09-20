import { describe, expect, it } from "vitest";

import {
  mentionLink,
  mentionedIds,
  mentionsToHtml,
  renderMentions,
} from "@/lib/mentions";

const PEOPLE = [
  { id: 3, display_name: "Léa Chen" },
  { id: 12, display_name: "Nino Garo" },
];

describe("mentionLink", () => {
  it("carries the person by id, and the name only to be read", () => {
    expect(mentionLink(12, "Nino Garo")).toBe("@[Nino Garo](mention://user/12)");
  });
});

describe("mentionedIds", () => {
  it("finds nobody in a plain message", () => {
    expect(mentionedIds("Revue faite.")).toEqual([]);
  });

  it("reads the ids, in the order they were written, once each", () => {
    const body = `${mentionLink(3, "Léa")} et ${mentionLink(12, "Nino")}, puis ${mentionLink(3, "Léa")}`;

    expect(mentionedIds(body)).toEqual([3, 12]);
  });

  it("is not fooled by a link that merely looks like one", () => {
    expect(mentionedIds("[le projet](https://waat.tools/user/12)")).toEqual([]);
  });
});

describe("renderMentions", () => {
  it("leaves a message naming nobody alone", () => {
    expect(renderMentions("Revue faite.", PEOPLE)).toBe("Revue faite.");
  });

  it("reads the name from the register rather than from the text", () => {
    // What was typed is stale; the register is what knows who id 12 is now.
    const body = "Merci @[Ancien Nom](mention://user/12) !";

    expect(renderMentions(body, PEOPLE)).toBe("Merci **@Nino Garo** !");
  });

  it("keeps the name that was written once the account is gone", () => {
    const body = "Merci @[Parti Depuis](mention://user/99) !";

    expect(renderMentions(body, PEOPLE)).toBe("Merci **@Parti Depuis** !");
  });
});

describe("mentionsToHtml", () => {
  it("leaves a message naming nobody alone", () => {
    expect(mentionsToHtml("Revue faite.")).toBe("Revue faite.");
  });

  it("turns a written mention into the node the editor knows", () => {
    expect(mentionsToHtml("Merci @[Nino Garo](mention://user/12) !")).toBe(
      'Merci <span data-type="mention" data-id="12" data-label="Nino Garo"></span> !',
    );
  });

  it("escapes what a name might carry", () => {
    expect(mentionsToHtml('@[A"B](mention://user/1)')).toContain(
      'data-label="A&quot;B"',
    );
  });
});
