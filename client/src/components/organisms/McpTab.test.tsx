import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { McpTab } from "@/components/organisms/McpTab";
import { MCP_URL } from "@/lib/mcp";

describe("McpTab", () => {
  it("gives the address a client connects to", () => {
    render(<McpTab />);
    expect(screen.getByText(MCP_URL)).toBeInTheDocument();
  });

  it("names the three clients the team uses", () => {
    render(<McpTab />);
    expect(screen.getByRole("heading", { name: "Claude Code" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Codex" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Gemini CLI" })).toBeInTheDocument();
  });

  it("says in French which boxes the key must carry", () => {
    render(<McpTab />);
    // Read twice over: once as what to ask a manager for, once beside the
    // tool that opens it. Either reading is an answer.
    expect(screen.getAllByText("Projets (lecture)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Temps (lecture)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Journal (lecture)").length).toBeGreaterThan(0);
  });

  it("says what each tool answers", () => {
    render(<McpTab />);
    expect(screen.getByText("find_project")).toBeInTheDocument();
    expect(screen.getByText("my_month")).toBeInTheDocument();
    expect(screen.getByText("what_changed")).toBeInTheDocument();
  });

  it("hands a snippet over rather than leaving it to be retyped", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(<McpTab />);
    await userEvent.click(
      screen.getByRole("button", { name: "Copier la configuration Codex" }),
    );

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("[mcp_servers.ganesh]"),
    );
  });
});
