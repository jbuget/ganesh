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
 * A mission's sheet and its changes.
 *
 * Every change is saved then read back from the server: the sheet is edited
 * field by field, with no \u00ab Enregistrer \u00bb button, and the screen must
 * never show anything other than what is in the database.
 */
export function useProjectDetail(
  projectId: number,
  /** Called after every write: the screen one came from may depend on it. */
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
    // The guard avoids writing into an already unmounted component, when one
    // leaves the sheet before the response comes back.
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

    /** Partial change: only the fields provided are applied. */
    async changerCaracteristiques(champs: {
      category?: ProjectCategory | null;
      priority?: ProjectPriority | null;
      estimated_days?: number | null;
    }) {
      await updateProject(projectId, champs);
      await reload();
    },

    /**
     * Takes the mission out of the reference list without losing anything: the
     * list no longer shows it, but entries already booked stay readable.
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
