import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { SignInPage } from "./SignInPage";

const params = vi.hoisted(() => ({ value: new URLSearchParams() }));

vi.mock("next/navigation", () => ({
  useSearchParams: () => params.value,
}));

function signInPage({ entra, at = "" }: { entra: boolean; at?: string }) {
  params.value = new URLSearchParams(at);
  render(<SignInPage entra={entra} />);
}

describe("SignInPage", () => {
  it("offers Microsoft when that is the door", () => {
    signInPage({ entra: true });

    expect(
      screen.getByRole("link", { name: "Se connecter avec Microsoft" }),
    ).toHaveAttribute("href", "/api/auth/login");
    expect(screen.queryByLabelText("Mot de passe")).not.toBeInTheDocument();
  });

  it("offers a login and a password when Entra is not there", () => {
    signInPage({ entra: false });

    expect(screen.getByLabelText("Identifiant")).toBeInTheDocument();
    expect(screen.getByLabelText("Mot de passe")).toHaveAttribute("type", "password");
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  /** Signing in must bring the person back where they were turned away. */
  it("carries where they were headed through the Microsoft door", () => {
    signInPage({ entra: true, at: "from=/users?name=ALICE" });

    expect(screen.getByRole("link")).toHaveAttribute(
      "href",
      "/api/auth/login?from=%2Fusers%3Fname%3DALICE",
    );
  });

  it("carries it through the fallback door too", () => {
    signInPage({ entra: false, at: "from=/users" });

    expect(document.querySelector('input[name="from"]')).toHaveValue("/users");
  });

  it("says why the sign-in did not go through", () => {
    signInPage({ entra: false, at: "reason=credentials" });

    expect(
      screen.getByText("Identifiant ou mot de passe incorrect."),
    ).toBeInTheDocument();
  });

  /** A replayed identity token lands here: it must read as something to redo. */
  it("says so when the token does not answer the sign-in asked for", () => {
    signInPage({ entra: true, at: "reason=nonce" });

    expect(
      screen.getByText(
        "Cette connexion ne correspond pas à celle demandée ici. Reprenez-la.",
      ),
    ).toBeInTheDocument();
  });

  /** A reason we never wrote down still has to say something. */
  it("falls back on a plain sentence for a reason it does not know", () => {
    signInPage({ entra: true, at: "reason=something-else" });

    expect(
      screen.getByText("La connexion n'a pas abouti. Réessayez."),
    ).toBeInTheDocument();
  });

  it("says nothing when nothing went wrong", () => {
    signInPage({ entra: true });

    expect(screen.queryByText(/réessayez/i)).not.toBeInTheDocument();
  });
});
