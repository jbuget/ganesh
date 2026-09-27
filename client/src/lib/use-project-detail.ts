"use client";

import { useCallback, useEffect, useState } from "react";

import type {
  Department,
  LinkIcon,
  ProjectCategory,
  ProjectDetailResponse,
  ProjectPriority,
  ProjectStatus,
  SubProjectPolicy,
} from "@/lib/api/generated/model";
import {
  addProjectLink,
  archiveProject,
  attachProject,
  changeProjectStatus,
  createProject,
  deleteProject,
  detachProject,
  getProjectDetail,
  removeProjectLink,
  unarchiveProject,
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
        go_live_date?: string | null;
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
     *
     * `subProjects` answers for the slices of a project cut into packages, and
     * the server refuses the exit without it: a package left behind would hold
     * its rank in the plan on behalf of a project that has gone.
     */
    async archive(subProjects?: SubProjectPolicy) {
      await archiveProject(projectId, { sub_projects: subProjects ?? null });
      await reload();
    },

    /**
     * Puts the mission back into the reference list, forgetting when it left.
     *
     * It comes back on its own: packages archived with it carry their own exit
     * date, and are brought back one by one.
     */
    async unarchive() {
      await unarchiveProject(projectId);
      await reload();
    },

    /**
     * Takes a mission that never served out of the reference list for good.
     *
     * Nothing is read back: the sheet no longer exists. It is up to the screen
     * that opened it to go somewhere else — reloading here would only find a
     * 404.
     */
    async remove() {
      await deleteProject(projectId);
      await onWrite?.();
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
     * Makes the mission a work package of another project.
     *
     * Nothing else moves: the phase, the estimate and the days already
     * declared stay on it, and the project it joins reads their sum.
     */
    async attachTo(parentId: number) {
      await attachProject(projectId, { parent_id: parentId });
      await reload();
    },

    /** Makes the work package a project of its own again. */
    async detach() {
      await detachProject(projectId);
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
