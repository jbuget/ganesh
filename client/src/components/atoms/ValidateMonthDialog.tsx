"use client";

import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { formatTotal } from "@/lib/dates";

interface ValidateMonthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mois: string;
  totalSaisi: number;
  joursOuvres: number;
  onConfirm: () => Promise<void>;
}

/**
 * Confirmation avant verrouillage d'un mois.
 *
 * Le recapitulatif est affiche avant la decision : le controle de completude
 * fait la qualite de la donnee, mieux qu'un blocage qui pousserait a remplir
 * n'importe quoi.
 */
export function ValidateMonthDialog({
  open,
  onOpenChange,
  mois,
  totalSaisi,
  joursOuvres,
  onConfirm,
}: ValidateMonthDialogProps) {
  const manquant = Math.max(0, joursOuvres - totalSaisi);
  const [enCours, setEnCours] = useState(false);

  /**
   * Le dialogue se referme lui-meme une fois le mois verrouille : rien dans la
   * confirmation ne ferme la fenetre, et l'echec doit rester sous les yeux.
   */
  async function confirmer() {
    if (enCours) return;
    setEnCours(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="capitalize">Valider {mois} ?</AlertDialogTitle>
          <AlertDialogDescription>
            Après validation, vous ne pourrez plus modifier ce mois. Seul un manager
            pourra le rouvrir.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted-foreground">Total saisi</dt>
          <dd className="text-right font-medium">{formatTotal(totalSaisi)} jour(s)</dd>
          <dt className="text-muted-foreground">Jours ouvrés</dt>
          <dd className="text-right font-medium">{joursOuvres} jours</dd>
        </dl>

        {manquant > 0 && (
          <p className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Il manque {formatTotal(manquant)} jour(s) pour couvrir le mois.
          </p>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel>Annuler</AlertDialogCancel>
          <AlertDialogAction onClick={confirmer} disabled={enCours}>
            Valider
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
