"use client";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ChooseActivityDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The mission being added, named so the choice reads in context. */
  mission: string;
  activities: { id: number; label: string }[];
  onChoose: (activityId: number) => void | Promise<void>;
}

/**
 * Which trade a mission is about to be declared under.
 *
 * Only ever opened when there is a choice to make: a mission carrying a
 * single trade is added without asking, because a dialog offering one button
 * is a click taken from the reader for nothing.
 *
 * The trade is asked rather than guessed. It could be read off the person —
 * a developer declares development — but that is exactly what falls apart
 * the week somebody stands in for the project manager, which is the whole
 * reason the level exists.
 */
export function ChooseActivityDialog({
  open,
  onOpenChange,
  mission,
  activities,
  onChoose,
}: ChooseActivityDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sous quelle activité ?</AlertDialogTitle>
          <AlertDialogDescription>
            « {mission} » est découpé en plusieurs activités. Choisissez celle sous
            laquelle vous allez déclarer votre temps.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <ul className="flex flex-col gap-1.5">
          {activities.map((activity) => (
            <li key={activity.id}>
              <button
                type="button"
                onClick={() => void onChoose(activity.id)}
                className="w-full cursor-pointer rounded-md border border-slate-300 px-3 py-2 text-left text-sm transition-colors hover:border-slate-400 hover:bg-slate-50"
              >
                {activity.label}
              </button>
            </li>
          ))}
        </ul>

        <AlertDialogFooter>
          <AlertDialogCancel className="cursor-pointer">Annuler</AlertDialogCancel>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
