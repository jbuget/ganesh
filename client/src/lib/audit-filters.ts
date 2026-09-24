import type { AuditAction } from "@/lib/api/generated/model";

/**
 * What a reader narrowed the register down to.
 *
 * Read across, the register is mostly declared time — thousands of lines a
 * month, and none of them what one opens this screen for. The criteria are
 * what make it answerable: a gesture, a person, a period.
 */
export interface AuditFilters {
  /** The gestures kept. Empty is every gesture, as an empty criterion is. */
  actions: AuditAction[];
  /** Whose gestures, by id. Empty is everyone's. */
  actorIds: string[];
  /** Days, both included. Empty is « since always » and « until now ». */
  fromDay: string;
  toDay: string;
}

export const NO_FILTER: AuditFilters = {
  actions: [],
  actorIds: [],
  fromDay: "",
  toDay: "",
};

export function hasAnyFilter(filters: AuditFilters): boolean {
  return (
    filters.actions.length > 0 ||
    filters.actorIds.length > 0 ||
    filters.fromDay !== "" ||
    filters.toDay !== ""
  );
}

/**
 * One family of gestures, as the picker offers them.
 *
 * Thirty gestures in one flat list is a list nobody reads to the end. Grouped
 * the way the product is divided, a reader looks up « les projets » and finds
 * « a supprimé le projet » where they expected it.
 *
 * The families are the reader's, not the API's: `project.assign` steers a
 * mission and sits under « Projets », though it is a person that moved.
 */
export interface ActionFamily {
  label: string;
  actions: { value: AuditAction; label: string }[];
}

export const ACTION_FAMILIES: ActionFamily[] = [
  {
    label: "Projets",
    actions: [
      { value: "project.create", label: "Création" },
      { value: "project.update", label: "Modification" },
      { value: "project.status_change", label: "Changement de phase" },
      { value: "project.delete", label: "Suppression" },
      { value: "project.assign", label: "Ajout d'un contributeur" },
      { value: "project.unassign", label: "Retrait d'un contributeur" },
    ],
  },
  {
    label: "Temps déclaré",
    actions: [
      { value: "entry.set", label: "Déclaration" },
      { value: "entry.clear", label: "Effacement" },
    ],
  },
  {
    label: "Mois",
    actions: [
      { value: "month.validate", label: "Validation" },
      { value: "month.reopen", label: "Réouverture" },
      { value: "month.project_add", label: "Projet ajouté au mois" },
      { value: "month.project_remove", label: "Projet retiré du mois" },
    ],
  },
  {
    label: "Mises à jour et fichiers",
    actions: [
      { value: "update.post", label: "Mise à jour publiée" },
      { value: "update.edit", label: "Mise à jour modifiée" },
      { value: "update.remove", label: "Mise à jour supprimée" },
      { value: "attachment.add", label: "Fichier ajouté" },
      { value: "attachment.rename", label: "Fichier renommé" },
      { value: "attachment.remove", label: "Fichier supprimé" },
    ],
  },
  {
    label: "Collaborateurs",
    actions: [
      { value: "user.create", label: "Arrivée" },
      { value: "user.role_change", label: "Changement de rôle" },
      { value: "user.identity_update", label: "Fiche modifiée" },
      { value: "user.presence_declare", label: "Semaine déclarée" },
      { value: "user.reminder_choose", label: "Fréquence de rappel" },
      { value: "reminder.run", label: "Rappels envoyés" },
      { value: "user.deactivate", label: "Désactivation" },
      { value: "user.activate", label: "Réactivation" },
    ],
  },
  {
    label: "Clés d'API",
    actions: [
      { value: "api_key.create", label: "Création" },
      { value: "api_key.update", label: "Modification" },
      { value: "api_key.revoke", label: "Révocation" },
    ],
  },
  {
    label: "Autres",
    actions: [
      { value: "simulation.create", label: "Simulation enregistrée" },
      { value: "simulation.update", label: "Simulation modifiée" },
      { value: "simulation.delete", label: "Simulation supprimée" },
      { value: "gazette.generate", label: "Gazette générée" },
    ],
  },
];

/** Every gesture the picker offers, families flattened. */
export function everyOfferedAction(): AuditAction[] {
  return ACTION_FAMILIES.flatMap((family) =>
    family.actions.map((action) => action.value),
  );
}
