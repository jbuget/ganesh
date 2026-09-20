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

/**
 * The browser, as the fetcher needs it — so a test can hand it another one.
 *
 * `at` says where we are, or nothing when there is no browser at all.
 */
export interface Browser {
  at: () => string | null;
  goTo: (url: string) => void;
}

const THE_BROWSER: Browser = {
  at: () =>
    typeof window === "undefined"
      ? null
      : `${window.location.pathname}${window.location.search}`,
  goTo: (url) => {
    window.location.assign(url);
  },
};

/**
 * Back to the sign-in screen, remembering where the person was.
 *
 * A full page load rather than a router push: everything held in memory is
 * built on a session that is over, and keeping it would show stale screens
 * behind a sign-in that has not happened yet.
 */
export function signInAgain(browser: Browser = THE_BROWSER): void {
  const here = browser.at();
  if (here === null) return;
  // Already there: redirecting would only lose the reason shown on it.
  if (here.startsWith("/sign-in")) return;
  browser.goTo(`/sign-in?from=${encodeURIComponent(here)}`);
}

export const bffFetcher = async <T>(
  url: string,
  options?: RequestInit,
  browser: Browser = THE_BROWSER,
): Promise<T> => {
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
    // 401 is the BFF or the API saying the session is over. Nothing the
    // screen can do about it, so say it where it shows: on the sign-in page.
    // 403 is another matter — the person is known and simply not allowed.
    if (response.status === 401) signInAgain(browser);
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
