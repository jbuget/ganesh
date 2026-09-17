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
  ProjectResponse,
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

/** Le referentiel des missions. */
export function useProjects() {
  const query = useListProjects();
  return { ...query, projects: successOf<ProjectResponse[]>(query.data) ?? [] };
}

/** La matrice d'un mois, pour un collaborateur donne. */
export function useMonthGrid(mois: string, userId: number | null, enabled: boolean) {
  const query = useGetMonthGrid(
    { mois, ...(userId ? { user_id: userId } : {}) },
    { query: { enabled } },
  );
  return { ...query, grid: successOf<MonthGridResponse>(query.data) };
}
