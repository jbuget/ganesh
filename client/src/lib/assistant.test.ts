import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api/fetcher";

import {
  consultedProjects,
  nameTargets,
  projectInView,
  refusalOf,
  remarkNames,
  type MdNode,
} from "./assistant";

describe("the project in view", () => {
  it("is the one whose page is open", () => {
    expect(projectInView("/projects/12", "")).toBe(12);
  });

  it("is the one whose panel is open over a screen", () => {
    expect(projectInView("/kanban", "?mission=40&tab=updates")).toBe(40);
  });

  it("is the panel rather than the page behind it", () => {
    expect(projectInView("/projects/12", "?mission=40")).toBe(40);
  });

  it("is none on a screen that shows no project", () => {
    expect(projectInView("/timesheet", "")).toBeNull();
  });

  it("is none on the list of projects itself", () => {
    expect(projectInView("/projects", "")).toBeNull();
  });
});

describe("what the assistant says when it does not answer", () => {
  it("says it is unavailable when no model answers", () => {
    expect(refusalOf(new ApiError(503, "No model"))).toBe(
      "L'assistant est indisponible pour le moment. Réessayez plus tard.",
    );
  });

  it("says the conversation is over when it has had its exchanges", () => {
    expect(refusalOf(new ApiError(409, "over"))).toBe(
      "Cette conversation est terminée. Commencez-en une nouvelle.",
    );
  });

  it("says the question is refused when it is empty or too long", () => {
    expect(refusalOf(new ApiError(422, "too long"))).toBe(
      "Cette question ne peut pas être posée : elle est vide ou trop longue.",
    );
  });

  it("says something went wrong otherwise", () => {
    expect(refusalOf(new Error("network"))).toBe("L'assistant n'a pas pu répondre.");
  });
});

describe("the projects an answer was read from", () => {
  const missions = [
    { project: { id: 7, label: "WAATcher" } },
    { project: { id: 9, label: "WAATcher — Import" } },
  ];

  it("are named, in the order the answer read them", () => {
    expect(consultedProjects([9, 7], missions)).toEqual([
      { id: 9, label: "WAATcher — Import" },
      { id: 7, label: "WAATcher" },
    ]);
  });

  it("leave out one the list no longer names", () => {
    expect(consultedProjects([7, 99], missions)).toEqual([
      { id: 7, label: "WAATcher" },
    ]);
  });
});

describe("what the names an answer gives lead to", () => {
  const projects = [
    { id: 85, label: "EDIT", kind: "project" },
    { id: 8, label: "EDIT V2", kind: "work_package" },
    { id: 2, label: "Formation", kind: "off_project" },
    { id: 9, label: "D", kind: "project" },
  ];
  const people = [
    { id: 3, display_name: "David DEHE", first_name: "David", last_name: "Dehé" },
  ];

  it("lead a project to its sheet", () => {
    expect(nameTargets(projects, people).get("EDIT V2")).toBe("/projects/8");
  });

  it("lead a person to their panel, under either of their names", () => {
    const targets = nameTargets(projects, people);

    expect(targets.get("David DEHE")).toBe("/users?user=3");
    expect(targets.get("David Dehé")).toBe("/users?user=3");
  });

  it("leave off-project work alone: its labels are words of the language", () => {
    expect(nameTargets(projects, people).has("Formation")).toBe(false);
  });

  it("leave out a name too short to be told from a word", () => {
    expect(nameTargets(projects, people).has("D")).toBe(false);
  });

  it("keep a project's link when a person bears the same name", () => {
    const targets = nameTargets(
      [{ id: 1, label: "Ganesh", kind: "project" }],
      [{ id: 5, display_name: "Ganesh" }],
    );

    expect(targets.get("Ganesh")).toBe("/projects/1");
  });
});

describe("the names an answer gives, linked", () => {
  const targets = new Map([
    ["EDIT", "/projects/85"],
    ["EDIT V2", "/projects/8"],
    ["David DEHE", "/users?user=3"],
  ]);

  function paragraph(...children: MdNode[]): MdNode {
    return { type: "root", children: [{ type: "paragraph", children }] };
  }

  function linked(tree: MdNode): MdNode[] {
    remarkNames(targets)()(tree);
    return tree.children![0].children!;
  }

  it("turn a name in the text into a link to it", () => {
    expect(
      linked(paragraph({ type: "text", value: "EDIT est porté par David DEHE." })),
    ).toEqual([
      {
        type: "link",
        url: "/projects/85",
        children: [{ type: "text", value: "EDIT" }],
      },
      { type: "text", value: " est porté par " },
      {
        type: "link",
        url: "/users?user=3",
        children: [{ type: "text", value: "David DEHE" }],
      },
      { type: "text", value: "." },
    ]);
  });

  it("read the longest first, so a package is not taken for its project", () => {
    expect(linked(paragraph({ type: "text", value: "EDIT V2" }))).toEqual([
      {
        type: "link",
        url: "/projects/8",
        children: [{ type: "text", value: "EDIT V2" }],
      },
    ]);
  });

  it("read whole words only", () => {
    expect(linked(paragraph({ type: "text", value: "EDITION et CREDIT" }))).toEqual([
      { type: "text", value: "EDITION et CREDIT" },
    ]);
  });

  it("leave code alone", () => {
    const code = { type: "inlineCode", value: "EDIT" };

    expect(linked(paragraph(code))).toEqual([code]);
  });

  it("leave a link alone, whatever it says", () => {
    const link = {
      type: "link",
      url: "https://x.y/EDIT",
      children: [{ type: "text", value: "EDIT" }],
    };

    expect(linked(paragraph(link))).toEqual([link]);
  });

  it("reach the names under emphasis", () => {
    const tree = paragraph({
      type: "emphasis",
      children: [{ type: "text", value: "EDIT V2" }],
    });

    expect(linked(tree)[0].children![0]).toMatchObject({
      type: "link",
      url: "/projects/8",
    });
  });
});
