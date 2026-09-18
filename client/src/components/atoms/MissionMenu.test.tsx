import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MissionMenu } from "./MissionMenu";

describe("MissionMenu", () => {
  it("keeps its actions folded until they are asked for", () => {
    render(
      <MissionMenu archivee={false} onArchiver={vi.fn()} onDesarchiver={vi.fn()} />,
    );

    expect(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });

  it("offers to archive the mission", async () => {
    render(
      <MissionMenu archivee={false} onArchiver={vi.fn()} onDesarchiver={vi.fn()} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );

    expect(screen.getByRole("button", { name: "Archiver" })).toBeInTheDocument();
  });

  it("archives the mission when the action is chosen", async () => {
    const archiver = vi.fn();
    render(
      <MissionMenu archivee={false} onArchiver={archiver} onDesarchiver={vi.fn()} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Archiver" }));

    expect(archiver).toHaveBeenCalledTimes(1);
  });

  it("closes the menu once the action is chosen", async () => {
    render(
      <MissionMenu archivee={false} onArchiver={vi.fn()} onDesarchiver={vi.fn()} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Archiver" }));

    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });
  it("offers to unarchive a mission already out of the reference list", async () => {
    render(<MissionMenu archivee onArchiver={vi.fn()} onDesarchiver={vi.fn()} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );

    expect(screen.getByRole("button", { name: "Désarchiver" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });

  it("puts the mission back in the reference list when the action is chosen", async () => {
    const desarchiver = vi.fn();
    render(<MissionMenu archivee onArchiver={vi.fn()} onDesarchiver={desarchiver} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Désarchiver" }));

    expect(desarchiver).toHaveBeenCalledTimes(1);
  });
});
