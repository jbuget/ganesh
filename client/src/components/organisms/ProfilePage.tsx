"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { ReminderCadenceField } from "@/components/atoms/ReminderCadenceField";
import { PageLayout } from "@/components/organisms/PageLayout";
import { departmentLabel } from "@/lib/departments";
import { roleLabel } from "@/lib/roles";
import { useProfileScreen } from "@/lib/use-profile";
import { useMayWrite } from "@/lib/use-may-write";

/**
 * One's own profile: who one is, and how one wants to be written to.
 *
 * Not in the sidebar's list of screens. One reaches it from behind one's own
 * name at the foot of the bar, where what concerns oneself already lives —
 * putting it in the navigation would make a personal setting read as one more
 * function of the product, beside « Projets » and « Journal ».
 *
 * The identity is shown and not edited. Who somebody is and where they work is
 * a manager's gesture, on the teammates screen; repeating the form here would
 * give two places to write one thing. What is one's own to decide is what one
 * finds here.
 */
export function ProfilePage() {
  const mayWrite = useMayWrite();
  const { user, isLoading, isSaving, choose } = useProfileScreen();

  const header = (
    <PageHeader
      title="Mon profil"
      subtitle="Ce que Ganesh sait de vous, et comment il vous écrit."
    />
  );

  if (isLoading || !user) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">Chargement…</p>
      </PageLayout>
    );
  }

  return (
    <PageLayout header={header}>
      <div className="flex max-w-2xl flex-col gap-8">
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold">Identité</h2>

          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex gap-3">
              <dt className="w-32 shrink-0 text-slate-500">Nom</dt>
              <dd className="min-w-0">{user.display_name}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-32 shrink-0 text-slate-500">Adresse</dt>
              <dd className="min-w-0 break-all">{user.email}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-32 shrink-0 text-slate-500">Rôle</dt>
              <dd className="min-w-0">{roleLabel(user.role)}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-32 shrink-0 text-slate-500">Pôle</dt>
              <dd className="min-w-0">
                {user.department ? (
                  departmentLabel(user.department)
                ) : (
                  <span className="text-slate-500">Non renseigné</span>
                )}
              </dd>
            </div>
          </dl>

          <p className="text-xs text-slate-500">
            Ces informations viennent de votre compte Microsoft et de la fiche tenue par
            les managers. Pour les corriger, demandez à un manager.
          </p>
        </section>

        {/* A guest is written to about nothing, so there is no cadence to
            choose: the section goes rather than sits there refusing. */}
        {mayWrite && (
          <section className="flex flex-col gap-3">
            <div>
              <h2 className="text-sm font-semibold">Rappels par e-mail</h2>
              <p className="text-sm text-slate-500">
                La cloche ne prévient que si Ganesh est ouvert. Un e-mail récapitule ce
                qui vous attend, sans jamais reprendre ce que vous avez déjà lu.
              </p>
            </div>

            <ReminderCadenceField
              value={user.reminder_cadence}
              onChange={(cadence) => void choose(cadence)}
              isSaving={isSaving}
            />

            <p aria-live="polite" className="min-h-4 text-xs text-slate-500">
              {isSaving ? "Enregistrement…" : "Votre choix est enregistré aussitôt."}
            </p>
          </section>
        )}
      </div>
    </PageLayout>
  );
}
