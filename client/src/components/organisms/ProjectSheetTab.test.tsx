import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProjectSheetTab } from "@/components/organisms/ProjectSheetTab";
import type { ProjectDetailResponse } from "@/lib/api/generated/model";

vi.mock("@/lib/api/queries", () => ({ useProjects: () => ({ missions: [] }) }));

const detail = ({
  project = {},
  ...rest
}: { project?: Record<string, unknown> } & Record<string, unknown> = {}) =>
  ({
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "operations",
      is_active: true,
      is_published: false,
      slug: null,
      summary: null,
      description: null,
      criticality: null,
      service_type: null,
      hosting: null,
      has_microsoft_entra: false,
      team: null,
      slack_channel: null,
      production_link: null,
      staging_link: null,
      repository_link: null,
      documentation_link: null,
      project_management_link: null,
      monitoring_link: null,
      stats_page_link: null,
      stats_api_link: null,
      ...project,
    },
    links: [],
    stack: [],
    tags: [],
    dependencies: [],
    ...rest,
  }) as unknown as ProjectDetailResponse;

function sheet(overrides: Record<string, unknown> = {}, handlers = {}) {
  const props = {
    updateFields: vi.fn().mockResolvedValue(undefined),
    saveDescription: vi.fn().mockResolvedValue(undefined),
    saveRegistry: vi.fn().mockResolvedValue(undefined),
    addLink: vi.fn().mockResolvedValue(undefined),
    removeLink: vi.fn().mockResolvedValue(undefined),
    ...handlers,
  };
  render(<ProjectSheetTab detail={detail(overrides)} editable {...props} />);
  return props;
}

describe("ProjectSheetTab", () => {
  it("lays the sheet out in the sections the catalogue reads", () => {
    sheet();

    // No section repeats the tab's own name: the tab is « Catalogue », and
    // what the service hangs from is « Rattachement ».
    for (const section of [
      "Publication",
      "Fiche",
      "Liens",
      "Technique",
      "Rattachement",
    ]) {
      expect(screen.getByText(section)).toBeInTheDocument();
    }
  });

  it("asks for each named address under the name the catalogue uses", () => {
    sheet();

    for (const label of [
      "Production",
      "Staging",
      "Code",
      "Documentation",
      "Monitoring",
      "Gestion de projet",
      "Page stats",
      "Données stats",
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
  });

  describe("publication", () => {
    it("says what is still missing rather than letting the server refuse", () => {
      sheet();

      expect(
        screen.getByText("Il manque le slug, le résumé, la criticité et le type."),
      ).toBeInTheDocument();
    });

    it("holds the switch back while the sheet is incomplete", () => {
      sheet();

      expect(
        screen.getByRole("switch", { name: "Publier au catalogue" }),
      ).toBeDisabled();
    });

    it("lets the mission be published once the sheet is complete", async () => {
      const { updateFields } = sheet({
        project: {
          slug: "portail",
          summary: "Un portail.",
          criticality: "standard",
          service_type: "fullstack",
        },
      });

      await userEvent.click(
        screen.getByRole("switch", { name: "Publier au catalogue" }),
      );

      expect(updateFields).toHaveBeenCalledWith({ is_published: true });
    });

    it("offers the address the label would give, while none is set", async () => {
      const { updateFields } = sheet();

      await userEvent.click(screen.getByRole("button", { name: "portail-bailleurs" }));

      expect(updateFields).toHaveBeenCalledWith({ slug: "portail-bailleurs" });
    });

    it("stops offering one once an address is chosen", () => {
      sheet({ project: { slug: "autre-chose" } });

      expect(
        screen.queryByRole("button", { name: "portail-bailleurs" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("catalogue lists", () => {
    it("sends the three lists together when one of them changes", async () => {
      const { saveRegistry } = sheet();

      await userEvent.click(screen.getByRole("button", { name: "Stack" }));
      await userEvent.type(screen.getByLabelText("Stack"), "Next.js");
      await userEvent.tab();

      expect(saveRegistry).toHaveBeenCalledWith({
        stack: ["Next.js"],
        tags: [],
        depends_on: [],
      });
    });

    it("leaves the other lists as they were", async () => {
      const { saveRegistry } = sheet({ stack: ["Python"], tags: ["ia"] });

      await userEvent.click(screen.getByRole("button", { name: "Tags" }));
      await userEvent.type(screen.getByLabelText("Tags"), "monitoring");
      await userEvent.tab();

      expect(saveRegistry).toHaveBeenCalledWith({
        stack: ["Python"],
        tags: ["ia", "monitoring"],
        depends_on: [],
      });
    });
  });

  it("writes a named address on the field it belongs to", async () => {
    const { updateFields } = sheet();

    await userEvent.click(screen.getByRole("button", { name: "Code" }));
    await userEvent.type(
      screen.getByLabelText("Code"),
      "https://github.com/waat-fr/portail",
    );
    await userEvent.tab();

    expect(updateFields).toHaveBeenCalledWith({
      repository_link: "https://github.com/waat-fr/portail",
    });
  });
});

describe("cancelling a field", () => {
  it("does not let Escape reach the panel behind", async () => {
    const onEscape = vi.fn();
    render(
      <div onKeyDown={onEscape}>
        <ProjectSheetTab
          editable
          detail={detail()}
          updateFields={vi.fn().mockResolvedValue(undefined)}
          saveDescription={vi.fn().mockResolvedValue(undefined)}
          saveRegistry={vi.fn().mockResolvedValue(undefined)}
          addLink={vi.fn().mockResolvedValue(undefined)}
          removeLink={vi.fn().mockResolvedValue(undefined)}
        />
      </div>,
    );

    await userEvent.click(screen.getAllByRole("button", { name: "Résumé" })[0]);
    await userEvent.keyboard("{Escape}");

    expect(onEscape).not.toHaveBeenCalled();
  });
});

describe("the slug", () => {
  it("shows the address it completes, so one sees what is being typed", () => {
    sheet({ project: { slug: "lorem-ipsum" } });

    expect(screen.getByText("waat.tools/services/")).toBeInTheDocument();
  });

  it("shows that address on an empty field too: that is where one wonders", () => {
    sheet();

    expect(screen.getByRole("button", { name: "Slug" })).toHaveTextContent(
      "waat.tools/services/portail-bailleurs",
    );
  });

  it("refuses a pasted URL where the catalogue expects a slug", async () => {
    const { updateFields } = sheet();

    await userEvent.click(screen.getAllByRole("button", { name: "Slug" })[0]);
    await userEvent.type(
      screen.getByRole("textbox", { name: "Slug" }),
      "https://lorem-ipsum.waat.tools{Enter}",
    );

    expect(updateFields).not.toHaveBeenCalled();
    expect(screen.getByText(/pas une URL entière/)).toBeInTheDocument();
  });

  it("writes a slug the catalogue can read", async () => {
    const { updateFields } = sheet();

    await userEvent.click(screen.getAllByRole("button", { name: "Slug" })[0]);
    await userEvent.type(
      screen.getByRole("textbox", { name: "Slug" }),
      "lorem-ipsum{Enter}",
    );

    expect(updateFields).toHaveBeenCalledWith({ slug: "lorem-ipsum" });
  });
});
