/**
 * The front end's single HTTP client, injected into the code Orval generates.
 *
 * Every request goes through the BFF (`/api/v1/...`), never straight to
 * FastAPI: the Entra token stays server-side, in an httpOnly session.
 *
 * Orval expects a response shaped `{ data, status, headers }`. HTTP errors are
 * turned into exceptions, otherwise React Query would take them for successes.
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
