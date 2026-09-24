import { Eye } from "lucide-react";

/**
 * The band that says an account reads without writing.
 *
 * It names what is missing — rights — and who hands them out: « refusé » with
 * no way forward is a dead end. Who reads it is not its business: the frame
 * decides that.
 */
export function ReadOnlyNotice() {
  return (
    <div
      role="status"
      className="flex items-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900"
    >
      <Eye className="size-4 shrink-0" aria-hidden />
      <span>
        Votre compte lit Ganesh sans y écrire. Demandez vos droits à un manager pour
        saisir vos temps.
      </span>
    </div>
  );
}
