"use client";

import { PageHeader } from "@/components/atoms/PageHeader";
import { WiringMark } from "@/components/atoms/WiringMark";
import { PageLayout } from "@/components/organisms/PageLayout";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { usePlatform } from "@/lib/api/queries";
import { doorDetail, doorLabel, serviceLabel, serviceSays } from "@/lib/platform";
import {
  NAMING_CELL,
  NAMING_CONTENT,
  STRONG_SEPARATOR,
  TABLE_FRAME,
  TABLE_HEADER,
} from "@/lib/table-frame";

/**
 * The platform, read and not steered.
 *
 * Administrators only, and the whole screen is the permission: there is no
 * reading here a manager may have, which is why the sidebar hides it rather
 * than showing it and refusing.
 *
 * Nothing is changeable, and that is the design rather than a first version.
 * The model, its key, the mail server and the bucket are configured in the
 * environment and nowhere else — a screen offering to change them would be
 * offering something it cannot do, and a key the application could hand back
 * is a key worth stealing. What this screen answers is the question one
 * actually opens it with: « est-ce que tout est branché ? »
 */
export function AdminPage() {
  const { platform, isLoading } = usePlatform();

  const header = (
    <PageHeader
      title="Administration"
      subtitle="Comment Ganesh est branché. En lecture seule : tout se configure dans l'environnement."
    />
  );

  if (isLoading) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">Chargement…</p>
      </PageLayout>
    );
  }

  if (!platform) {
    return (
      <PageLayout header={header}>
        <p className="text-sm text-slate-500">
          La plateforme n&apos;a pas pu être lue.
        </p>
      </PageLayout>
    );
  }

  return (
    <PageLayout header={header}>
      <div className="max-w-[900px] space-y-8">
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Connexion</h2>
          <div className="[&_[data-slot=table-container]]:overflow-visible">
            <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
              <TableHeader className={TABLE_HEADER}>
                <TableRow>
                  <TableHead className={`w-64 ${STRONG_SEPARATOR}`}>
                    Ce qui est en place
                  </TableHead>
                  <TableHead>Ce que cela veut dire</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                <TableRow className="group bg-slate-50 hover:bg-slate-100">
                  <TableCell className={NAMING_CELL}>
                    <span className={NAMING_CONTENT}>Porte</span>
                  </TableCell>
                  <TableCell className="py-2 text-slate-600">
                    {doorLabel(platform.door)} — {doorDetail(platform.door)}
                  </TableCell>
                </TableRow>

                <TableRow className="group bg-slate-50 hover:bg-slate-100">
                  <TableCell className={NAMING_CELL}>
                    <span className={NAMING_CONTENT}>Environnement</span>
                  </TableCell>
                  <TableCell className="py-2 text-slate-600">
                    {platform.environment}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Services</h2>
          <div className="[&_[data-slot=table-container]]:overflow-visible">
            <Table className={`border-separate border-spacing-0 ${TABLE_FRAME}`}>
              <TableHeader className={TABLE_HEADER}>
                <TableRow>
                  <TableHead className={`w-64 ${STRONG_SEPARATOR}`}>Service</TableHead>
                  <TableHead className="w-36">État</TableHead>
                  <TableHead>Adresse, ou ce qu&apos;il manque</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {platform.services.map((service) => (
                  <TableRow
                    key={service.name}
                    className="group bg-slate-50 hover:bg-slate-100"
                  >
                    <TableCell className={NAMING_CELL}>
                      <span className={NAMING_CONTENT}>
                        {serviceLabel(service.name)}
                      </span>
                    </TableCell>
                    <TableCell className="py-2">
                      <WiringMark configured={service.configured} />
                    </TableCell>
                    <TableCell className="py-2 text-slate-600">
                      {serviceSays(service)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Said once, under the table, rather than on each line: two of the
              four services are optional by design, and « non câblé » on their
              row would otherwise read as something broken. */}
          <p className="text-xs text-slate-500">
            Un service non câblé ne casse rien : Ganesh fonctionne sans, en faisant
            moins. Tout se règle dans l&apos;environnement du serveur, puis au
            redémarrage.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Droits</h2>
          <p className="text-sm text-slate-600">
            Les rôles se donnent depuis l&apos;écran « Utilisateurs », où chaque
            personne porte le sien. Un manager promeut jusqu&apos;à manager ; seul un
            administrateur nomme un administrateur.
          </p>
        </section>
      </div>
    </PageLayout>
  );
}
