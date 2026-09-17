"use client";

import { useCallback, useEffect, useState } from "react";

import type {
  Department,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectStatus,
} from "@/lib/api/generated/model";
import {
  addProjectLink,
  changeProjectStatus,
  getProjectDetail,
  removeProjectLink,
  updateProject,
  updateProjectDescription,
  updateProjectDetail,
} from "@/lib/api/generated/projects/projects";

/**
 * La fiche d'une mission et ses modifications.
 *
 * Chaque changement est enregistre puis relu depuis le serveur : la fiche
 * s'edite champ par champ, sans bouton « Enregistrer », et l'ecran ne doit
 * jamais montrer autre chose que ce qui est en base.
 */
export function useProjectDetail(
  projectId: number,
  /** Appele apres chaque ecriture : l'ecran d'ou l'on vient peut en dependre. */
  onEcriture?: () => void | Promise<void>,
) {
  const [detail, setDetail] = useState<ProjectDetailResponse | null>(null);
  const [introuvable, setIntrouvable] = useState(false);

  const recharger = useCallback(async () => {
    try {
      const reponse = await getProjectDetail(projectId);
      setDetail(reponse.data as ProjectDetailResponse);
    } catch {
      setIntrouvable(true);
    }
    await onEcriture?.();
  }, [projectId, onEcriture]);

  useEffect(() => {
    // Le garde evite d'ecrire dans un composant deja demonte, quand on quitte
    // la fiche avant que la reponse ne revienne.
    let vivant = true;
    getProjectDetail(projectId)
      .then((reponse) => {
        if (vivant) setDetail(reponse.data as ProjectDetailResponse);
      })
      .catch(() => {
        if (vivant) setIntrouvable(true);
      });
    return () => {
      vivant = false;
    };
  }, [projectId]);

  return {
    detail,
    introuvable,
    recharger,

    async enregistrerFiche(departements: Department[], contactsMetier: string | null) {
      await updateProjectDetail(projectId, {
        departements,
        contacts_metier: contactsMetier,
      });
      await recharger();
    },

    async changerPhase(statut: ProjectStatus) {
      await changeProjectStatus(projectId, { statut });
      await recharger();
    },

    /** Modification partielle : seuls les champs fournis sont appliques. */
    async changerCaracteristiques(champs: {
      categorie?: ProjectCategory | null;
      estime_j?: number | null;
    }) {
      await updateProject(projectId, champs);
      await recharger();
    },

    async enregistrerDescription(description: string) {
      await updateProjectDescription(projectId, { description });
      await recharger();
    },

    async ajouterLien(label: string, url: string) {
      await addProjectLink(projectId, { label, url });
      await recharger();
    },

    async retirerLien(linkId: number) {
      await removeProjectLink(projectId, linkId);
      await recharger();
    },
  };
}
