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
  createProject,
  getProjectDetail,
  removeProjectLink,
  updateProject,
  updateProjectDescription,
  updateProjectDetail,
  updateProjectRegistry,
} from "@/lib/api/generated/projects/projects";
import type { SheetFields } from "@/lib/service-sheet";

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
  onWrite?: () => void | Promise<void>,
) {
  const [detail, setDetail] = useState<ProjectDetailResponse | null>(null);
  const [notFound, setNotFound] = useState(false);

  const reload = useCallback(async () => {
    try {
      const response = await getProjectDetail(projectId);
      setDetail(response.data as ProjectDetailResponse);
    } catch {
      setNotFound(true);
    }
    await onWrite?.();
  }, [projectId, onWrite]);

  useEffect(() => {
    // The guard avoids writing into an already unmounted component, when one
    // leaves the sheet before the response comes back.
    let alive = true;
    getProjectDetail(projectId)
      .then((response) => {
        if (alive) setDetail(response.data as ProjectDetailResponse);
      })
      .catch(() => {
        if (alive) setNotFound(true);
      });
    return () => {
      alive = false;
    };
  }, [projectId]);

  return {
    detail,
    notFound,
    reload,

    async saveSheet(departments: Department[], businessContacts: string | null) {
      await updateProjectDetail(projectId, {
        departments,
        business_contacts: businessContacts,
      });
      await reload();
    },

    async rename(label: string) {
      await updateProject(projectId, { label });
      await reload();
    },

    async changePhase(status: ProjectStatus) {
      await changeProjectStatus(projectId, { status });
      await reload();
    },

    /** Partial change: only the fields provided are applied. */
    async updateFields(
      fields: SheetFields & {
        category?: ProjectCategory | null;
        priority?: ProjectPriority | null;
        estimated_days?: number | null;
      },
    ) {
      await updateProject(projectId, fields);
      await reload();
    },

    /**
     * The catalogue lists: stack, tags and dependencies.
     *
     * The three travel together, and each replaces what the server holds: the
     * screen shows them in full and sends back what it shows.
     */
    async saveRegistry(registry: {
      stack: string[];
      tags: string[];
      depends_on: number[];
    }) {
      await updateProjectRegistry(projectId, registry);
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
    async unarchive() {
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

    /**
     * Cuts the mission into a work package.
     *
     * A name is all that is asked: the package opens at the phase every mission
     * starts from, and is steered from its own sheet afterwards.
     */
    async addSubProject(label: string) {
      await createProject({
        label,
        kind: "work_package",
        status: "exploration",
        parent_id: projectId,
      });
      await reload();
    },
  };
}
