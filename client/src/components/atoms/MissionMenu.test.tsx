import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MissionMenu } from "./MissionMenu";

describe("MissionMenu", () => {
  it("garde ses actions repliées tant qu'on ne les demande pas", () => {
    render(
      <MissionMenu archivee={false} onArchiver={vi.fn()} onDesarchiver={vi.fn()} />,
    );

    expect(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });

  it("propose d'archiver la mission", async () => {
    render(
      <MissionMenu archivee={false} onArchiver={vi.fn()} onDesarchiver={vi.fn()} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );

    expect(screen.getByRole("button", { name: "Archiver" })).toBeInTheDocument();
  });

  it("archive la mission au choix de l'action", async () => {
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

  it("referme le menu une fois l'action choisie", async () => {
    render(
      <MissionMenu archivee={false} onArchiver={vi.fn()} onDesarchiver={vi.fn()} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Archiver" }));

    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });
  it("propose de désarchiver une mission déjà sortie du référentiel", async () => {
    render(<MissionMenu archivee onArchiver={vi.fn()} onDesarchiver={vi.fn()} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );

    expect(screen.getByRole("button", { name: "Désarchiver" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });

  it("remet la mission au référentiel au choix de l'action", async () => {
    const desarchiver = vi.fn();
    render(<MissionMenu archivee onArchiver={vi.fn()} onDesarchiver={desarchiver} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Désarchiver" }));

    expect(desarchiver).toHaveBeenCalledTimes(1);
  });
});
