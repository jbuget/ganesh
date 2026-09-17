/**
 * Client HTTP unique du front, injecte dans le code genere par Orval.
 *
 * Toutes les requetes passent par le BFF (`/api/v1/...`), jamais directement
 * par FastAPI : le jeton Entra reste cote serveur, dans une session httpOnly.
 *
 * Orval attend une reponse de la forme `{ data, status, headers }`. Les erreurs
 * HTTP sont converties en exception, sans quoi React Query les prendrait pour
 * des succes.
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export const bffFetcher = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(url, { ...options, cache: "no-store" });
  const body = await response.text();
  const data = body ? JSON.parse(body) : undefined;

  if (!response.ok) {
    throw new ApiError(response.status, data?.detail ?? response.statusText);
  }

  return {
    data,
    status: response.status,
    headers: response.headers,
  } as T;
};
