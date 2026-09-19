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

/** The body as JSON, or nothing when it is not JSON at all. */
function parsed(body: string): unknown {
  if (!body) return undefined;
  try {
    return JSON.parse(body);
  } catch {
    return undefined;
  }
}

/** What the API says went wrong, when it says it the way FastAPI does. */
function detailOf(data: unknown): string | undefined {
  if (typeof data !== "object" || data === null) return undefined;
  const detail = (data as { detail?: unknown }).detail;
  return typeof detail === "string" ? detail : undefined;
}

export const bffFetcher = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(url, { ...options, cache: "no-store" });
  const body = await response.text();
  /*
    Parsed as a maybe, never as a given. A 500 comes back from FastAPI as plain
    text and a gateway answers in HTML: parsing before reading the status
    turned both into a `SyntaxError` pointing here, which said nothing of the
    call that failed nor of the status it came back with.
  */
  const data = parsed(body);

  if (!response.ok) {
    throw new ApiError(response.status, detailOf(data) ?? response.statusText);
  }

  // A body that came back whole but unreadable is still a failed call: better
  // said as such than handed on to React Query as data.
  if (body && data === undefined) {
    throw new ApiError(response.status, `Réponse illisible de ${url}`);
  }

  return {
    data,
    status: response.status,
    headers: response.headers,
  } as T;
};
