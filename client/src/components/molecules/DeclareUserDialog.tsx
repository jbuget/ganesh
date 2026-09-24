"use client";

import { useState } from "react";

import { OptionPicker } from "@/components/atoms/OptionPicker";
import { RolePicker } from "@/components/atoms/RolePicker";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { DeclareUserRequest, Department, Role } from "@/lib/api/generated/model";
import { DEPARTMENTS } from "@/lib/departments";

interface DeclareUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The ranks the reader may hand out — never above their own. */
  grantable: Role[];
  onConfirm: (declaration: DeclareUserRequest) => Promise<void>;
}

/**
 * Declaring somebody before their first sign-in.
 *
 * An account otherwise comes into being the day its owner signs in, at the
 * bottom of the ladder, and whoever is arriving on Monday can be put on no
 * project before then. Three things are asked for and none of them is
 * optional: the address, which is what the first sign-in is matched on, the
 * civil name, because declaring somebody is saying who they are, and the
 * rank, which this screen exists to hand out.
 */
export function DeclareUserDialog({
  open,
  onOpenChange,
  grantable,
  onConfirm,
}: DeclareUserDialogProps) {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState<Role>("TEAMMATE");
  const [department, setDepartment] = useState<Department | null>(null);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<string | null>(null);

  const isValid =
    email.trim().includes("@") &&
    firstName.trim().length > 0 &&
    lastName.trim().length > 0;

  function close(next: boolean) {
    if (!next) {
      setEmail("");
      setFirstName("");
      setLastName("");
      setRole("TEAMMATE");
      setDepartment(null);
      setRefusal(null);
    }
    onOpenChange(next);
  }

  async function confirm() {
    if (!isValid) return;
    setBusy(true);
    setRefusal(null);
    try {
      await onConfirm({
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        role,
        department,
      });
      close(false);
    } catch {
      // The address is the one thing the API can refuse on its own: an
      // account already exists at it, and a second could never be claimed.
      setRefusal("Un compte existe déjà à cette adresse.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Déclarer un utilisateur</DialogTitle>
          <DialogDescription>
            Le compte existera avant la première connexion : celle-ci le reprendra, à
            l&apos;adresse indiquée, sans en ouvrir un second.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="declare-email">Adresse e-mail</Label>
            <Input
              id="declare-email"
              type="email"
              value={email}
              autoFocus
              placeholder="n.arrivee@waat.fr"
              onChange={(event) => setEmail(event.target.value)}
            />
            {/* Said before the mistake, not after: an address Entra does not
                send leaves the declared account unclaimable. */}
            <p className="text-xs text-slate-500">
              Exactement l&apos;adresse du compte Microsoft, sans quoi la première
              connexion ouvrira un second compte.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-2">
              <Label htmlFor="declare-first-name">Prénom</Label>
              <Input
                id="declare-first-name"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="declare-last-name">Nom</Label>
              <Input
                id="declare-last-name"
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label>Rôle</Label>
            <RolePicker
              role={role}
              modifiable
              grantable={grantable}
              onChange={(next) => setRole(next)}
            />
          </div>

          <div className="grid gap-2">
            <Label>Pôle</Label>
            <OptionPicker
              value={department}
              options={DEPARTMENTS}
              label="Pôle"
              editable
              onChange={(next) => setDepartment(next)}
            />
          </div>
        </div>

        {refusal && <p className="text-sm text-rose-600">{refusal}</p>}

        <DialogFooter>
          <Button variant="outline" onClick={() => close(false)}>
            Annuler
          </Button>
          <Button onClick={confirm} disabled={!isValid || busy}>
            Déclarer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
