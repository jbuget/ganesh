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
 * field by field, with no « Enregistrer » button, and the screen must
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

    async saveSheet(departments: Department[], contactsMetier: string | null) {
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

    async changePhase(status: ProjectStatus) {
      await changeProjectStatus(projectId, { status });
      await reload();
    },

    /** Partial change: only the fields provided are applied. */
    async updateFields(fields: {
      category?: ProjectCategory | null;
      priority?: ProjectPriority | null;
      estimated_days?: number | null;
    }) {
      await updateProject(projectId, fields);
      await reload();
    },

    /**
     * Takes the mission out of the reference list without losing anything: the
     * list no longer shows it, but entries already booked stay readable.
     */
    async archive() {
      await updateProject(projectId, { is_active: false });
      await reload();
    },

    /** Puts the mission back into the reference list, forgetting when it left. */
    async desarchiver() {
      await updateProject(projectId, { is_active: true });
      await reload();
    },

    async saveDescription(description: string) {
      await updateProjectDescription(projectId, { description });
      await reload();
    },

    /** `icon` at `null`: the server infers it from the address. */
    async addLink(label: string, url: string, icon: LinkIcon | null) {
      await addProjectLink(projectId, { label, url, icon });
      await reload();
    },

    async removeLink(linkId: number) {
      await removeProjectLink(projectId, linkId);
      await reload();
    },
  };
}
