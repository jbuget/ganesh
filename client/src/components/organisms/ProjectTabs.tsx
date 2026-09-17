"use client";

import { ProjectPilotageTab } from "@/components/organisms/ProjectPilotageTab";
import { ProjectSheetTab } from "@/components/organisms/ProjectSheetTab";
import { ProjectUpdatesTab } from "@/components/organisms/ProjectUpdatesTab";
import { useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Department, ProjectDetailResponse } from "@/lib/api/generated/model";

interface ProjectTabsProps {
  detail: ProjectDetailResponse;
  onChange: () => void | Promise<void>;
  enregistrerFiche: (
    departements: Department[],
    contactsMetier: string | null,
  ) => Promise<void>;
  enregistrerDescription: (texte: string) => Promise<void>;
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
  onChange,
  enregistrerFiche,
  enregistrerDescription,
}: ProjectTabsProps) {
  // Fige l'heure de reference le temps de la consultation : « il y a 3 min »
  // ne doit pas se recalculer a chaque rendu, et le fil n'est de toute facon
  // charge qu'apres le montage — rien n'est rendu cote serveur.
  const [maintenant] = useState(() => new Date());

  return (
    <Tabs defaultValue="pilotage" className="gap-4">
      <TabsList>
        <TabsTrigger value="pilotage">Pilotage</TabsTrigger>
        <TabsTrigger value="updates">Mises à jour</TabsTrigger>
        <TabsTrigger value="fiche">Fiche service</TabsTrigger>
        <TabsTrigger value="audit">Journal</TabsTrigger>
      </TabsList>

      <TabsContent value="pilotage">
        <ProjectPilotageTab
          detail={detail}
          onChange={onChange}
          enregistrerFiche={enregistrerFiche}
        />
      </TabsContent>

      <TabsContent value="updates">
        <ProjectUpdatesTab projectId={detail.project.id} maintenant={maintenant} />
      </TabsContent>

      <TabsContent value="fiche">
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
