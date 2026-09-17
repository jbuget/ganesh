"use client";

import { useCallback, useEffect, useState } from "react";

import type { ProjectUpdateResponse } from "@/lib/api/generated/model";
import {
  editProjectUpdate,
  listProjectUpdates,
  postProjectUpdate,
  removeProjectUpdate,
} from "@/lib/api/generated/projects/projects";

/**
 * Le fil de suivi d'une mission.
 *
 * Chaque ecriture est relue depuis le serveur : c'est lui qui decide de la
 * chronologie, de ce qui reste visible d'une mise a jour retiree, et de qui a
 * le droit de la toucher.
 */
export function useProjectUpdates(
  projectId: number,
  /**
   * Appele apres chaque ecriture : le fil ne se lit pas qu'ici. Le referentiel
   * et le kanban annoncent son decompte et son dernier message, et resteraient
   * sur ce qu'ils savaient a l'ouverture du panneau.
   */
  onEcriture?: () => void | Promise<void>,
) {
  const [fil, setFil] = useState<ProjectUpdateResponse[] | null>(null);

  const recharger = useCallback(async () => {
    const reponse = await listProjectUpdates(projectId);
    setFil(reponse.data as ProjectUpdateResponse[]);
  }, [projectId]);

  useEffect(() => {
    let vivant = true;
    listProjectUpdates(projectId).then((reponse) => {
      if (vivant) setFil(reponse.data as ProjectUpdateResponse[]);
    });
    return () => {
      vivant = false;
    };
  }, [projectId]);

  return {
    fil,

    async publier(texte: string) {
      await postProjectUpdate(projectId, { texte });
      await recharger();
      await onEcriture?.();
    },

    async corriger(updateId: number, texte: string) {
      await editProjectUpdate(projectId, updateId, { texte });
      await recharger();
      await onEcriture?.();
    },

    async retirer(updateId: number) {
      await removeProjectUpdate(projectId, updateId);
      await recharger();
      await onEcriture?.();
    },
  };
}
