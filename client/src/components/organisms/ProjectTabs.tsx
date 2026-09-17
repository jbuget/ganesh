"use client";

import { ArchivedCallout } from "@/components/atoms/ArchivedCallout";
import { MissionMenu } from "@/components/atoms/MissionMenu";
import { ProjectPilotageTab } from "@/components/organisms/ProjectPilotageTab";
import { ProjectSheetTab } from "@/components/organisms/ProjectSheetTab";
import { ProjectUpdatesTab } from "@/components/organisms/ProjectUpdatesTab";
import { useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";

interface ProjectTabsProps {
  detail: ProjectDetailResponse;
  /** Sur quel onglet s'ouvrir ; le pilotage a defaut. */
  ongletInitial?: string | null;
  onChange: () => void | Promise<void>;
  enregistrerFiche: (
    departements: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
  enregistrerDescription: (texte: string) => Promise<void>;
  changerPhase: (statut: ProjectStatus) => Promise<void>;
  changerCaracteristiques: (champs: {
    categorie?: ProjectCategory | null;
    estime_j?: number | null;
  }) => Promise<void>;
  ajouterLien: (label: string, url: string, icone: LinkIcon | null) => Promise<void>;
  retirerLien: (linkId: number) => Promise<void>;
  archiver: () => Promise<void>;
  desarchiver: () => Promise<void>;
}

/** Ce qui reste a construire, annonce plutot que laisse vide. */
function Chantier({ quoi }: { quoi: string }) {
  return <p className="py-8 text-center text-sm text-slate-400">{quoi}</p>;
}

/**
 * Les quatre facettes d'une mission.
 *
 * Partagees par le panneau lateral et la fiche en pleine page : deux montages
 * du meme contenu, pour qu'ils ne divergent pas.
 */
export function ProjectTabs({
  detail,
  ongletInitial,
  onChange,
  enregistrerFiche,
  enregistrerDescription,
  changerPhase,
  changerCaracteristiques,
  ajouterLien,
  retirerLien,
  archiver,
  desarchiver,
}: ProjectTabsProps) {
  // Fige l'heure de reference le temps de la consultation : « il y a 3 min »
  // ne doit pas se recalculer a chaque rendu, et le fil n'est de toute facon
  // charge qu'apres le montage — rien n'est rendu cote serveur.
  const [maintenant] = useState(() => new Date());

  return (
    <Tabs
      defaultValue={ongletInitial ?? "pilotage"}
      className="flex min-h-0 flex-1 flex-col gap-4"
    >
      {/* Au-dessus des onglets, donc lu avant eux : l'etat de la mission
          conditionne tout ce qu'on s'apprete a faire dessus. */}
      {!detail.project.actif && (
        <ArchivedCallout archivedAt={detail.project.archived_at} />
      )}

      {/* Le menu se tient au bout des onglets, du cote ou le regard s'arrete :
          on choisit d'abord quoi lire, et ce qui agit sur la mission entiere
          attend a l'ecart. */}
      <div className="flex shrink-0 items-center gap-2">
        <TabsList className="min-w-0 flex-1">
          <TabsTrigger value="pilotage">Pilotage</TabsTrigger>
          <TabsTrigger value="updates">Mises à jour</TabsTrigger>
          <TabsTrigger value="fiche">Fiche service</TabsTrigger>
          <TabsTrigger value="audit">Journal</TabsTrigger>
        </TabsList>

        <MissionMenu
          archivee={!detail.project.actif}
          onArchiver={archiver}
          onDesarchiver={desarchiver}
        />
      </div>

      <TabsContent value="pilotage">
        <ProjectPilotageTab
          detail={detail}
          onChange={onChange}
          enregistrerFiche={enregistrerFiche}
          changerPhase={changerPhase}
          changerCaracteristiques={changerCaracteristiques}
          ajouterLien={ajouterLien}
          retirerLien={retirerLien}
        />
      </TabsContent>

      <TabsContent value="updates">
        <ProjectUpdatesTab
          projectId={detail.project.id}
          maintenant={maintenant}
          onChange={onChange}
          // Venu du decompte, on vient ecrire : le curseur attend deja dans
          // l'editeur. Venu du panneau, on vient d'abord lire.
          focusRedaction={ongletInitial === "updates"}
        />
      </TabsContent>

      <TabsContent value="fiche" className="min-h-0 flex-1">
        <ProjectSheetTab
          description={detail.project.description}
          onSave={enregistrerDescription}
        />
      </TabsContent>

      <TabsContent value="audit">
        <Chantier quoi="Le journal arrive." />
      </TabsContent>
    </Tabs>
  );
}
