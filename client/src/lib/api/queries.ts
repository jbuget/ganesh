/**
 * Enveloppes applicatives autour des hooks generes par Orval.
 *
 * Orval type `data` comme l'union du succes et des erreurs declarees dans
 * l'OpenAPI. Or `bffFetcher` leve une `ApiError` des que la reponse n'est pas
 * 2xx : lorsqu'un hook expose des donnees, ce sont donc toujours celles du
 * succes. Ce fichier est le seul endroit ou ce savoir est applique, plutot que
 * de disperser des conversions de type dans les composants.
 */
import { useGetMonthGrid } from "@/lib/api/generated/entries/entries";
import type {
  MonthGridResponse,
  ProjectListItemResponse,
  UserResponse,
} from "@/lib/api/generated/model";
import { useListProjects } from "@/lib/api/generated/projects/projects";
import { useGetMe, useListUsers } from "@/lib/api/generated/users/users";

function successOf<T>(response: { data: unknown } | undefined): T | undefined {
  return response?.data as T | undefined;
}

/** Meme raisonnement pour le resultat d'une mutation. */
export function mutationResult<T>(response: { data: unknown }): T {
  return response.data as T;
}

/** L'utilisateur courant. */
export function useCurrentUser() {
  const query = useGetMe();
  return { ...query, user: successOf<UserResponse>(query.data) };
}

/**
 * Les collaborateurs.
 *
 * Par defaut, seuls les actifs : partout ailleurs qu'a l'ecran de gestion, un
 * collaborateur desactive n'a plus a etre propose.
 */
export function useTeammates(includeInactive = false) {
  const query = useListUsers(includeInactive ? { include_inactive: true } : undefined);
  return { ...query, teammates: successOf<UserResponse[]>(query.data) ?? [] };
}

/**
 * Le referentiel des missions, chacune avec qui s'en occupe.
 *
 * Les affectations viennent de la meme requete que les missions : le
 * referentiel les aligne en colonnes, et une requete par ligne les ferait
 * arriver les unes apres les autres sous les yeux du lecteur.
 */
export function useProjects() {
  const query = useListProjects();
  const missions = successOf<ProjectListItemResponse[]>(query.data) ?? [];
  return {
    ...query,
    missions,
    /** Les seules missions, pour les ecrans qui ignorent les affectations. */
    projects: missions.map((mission) => mission.project),
  };
}

/** La matrice d'un mois, pour un collaborateur donne. */
export function useMonthGrid(mois: string, userId: number | null, enabled: boolean) {
  const query = useGetMonthGrid(
    { mois, ...(userId ? { user_id: userId } : {}) },
    { query: { enabled } },
  );
  return { ...query, grid: successOf<MonthGridResponse>(query.data) };
}
