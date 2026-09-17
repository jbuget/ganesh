"use client";

import { useCallback, useEffect, useState } from "react";

import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectPriority,
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

  const reload = useCallback(async () => {
    try {
      const response = await getProjectDetail(projectId);
      setDetail(response.data as ProjectDetailResponse);
    } catch {
      setIntrouvable(true);
    }
    await onEcriture?.();
  }, [projectId, onEcriture]);

  useEffect(() => {
    // Le garde evite d'ecrire dans un composant deja demonte, quand on quitte
    // la fiche avant que la reponse ne revienne.
    let alive = true;
    getProjectDetail(projectId)
      .then((response) => {
        if (alive) setDetail(response.data as ProjectDetailResponse);
      })
      .catch(() => {
        if (alive) setIntrouvable(true);
      });
    return () => {
      alive = false;
    };
  }, [projectId]);

  return {
    detail,
    introuvable,
    reload,

    async enregistrerFiche(departments: Department[], contactsMetier: string | null) {
      await updateProjectDetail(projectId, {
        departments,
        business_contacts: contactsMetier,
      });
      await reload();
    },

    async renommer(label: string) {
      await updateProject(projectId, { label });
      await reload();
    },

    async changerPhase(status: ProjectStatus) {
      await changeProjectStatus(projectId, { status });
      await reload();
    },

    /** Modification partielle : seuls les champs fournis sont appliques. */
    async changerCaracteristiques(champs: {
      category?: ProjectCategory | null;
      priority?: ProjectPriority | null;
      estimated_days?: number | null;
    }) {
      await updateProject(projectId, champs);
      await reload();
    },

    /**
     * Sort la mission du referentiel sans rien perdre : le referentiel ne la
     * liste plus, mais les saisies deja passees dessus restent lisibles.
     */
    async archiver() {
      await updateProject(projectId, { is_active: false });
      await reload();
    },

    /** Remet la mission au referentiel, et oublie la date de sa sortie. */
    async desarchiver() {
      await updateProject(projectId, { is_active: true });
      await reload();
    },

    async enregistrerDescription(description: string) {
      await updateProjectDescription(projectId, { description });
      await reload();
    },

    /** `icone` a `null` : le serveur la deduit de l'adresse. */
    async ajouterLien(label: string, url: string, icon: LinkIcon | null) {
      await addProjectLink(projectId, { label, url, icon });
      await reload();
    },

    async retirerLien(linkId: number) {
      await removeProjectLink(projectId, linkId);
      await reload();
    },
  };
}
