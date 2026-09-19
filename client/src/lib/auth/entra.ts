/**
 * What the BFF says to Entra, and how it reads what comes back.
 *
 * The BFF is the OAuth client here: it holds the secret, it exchanges the
 * code, it renews the session. The browser never talks to Entra except to
 * sign in, and never sees a token.
 *
 * The flow is authorization code with PKCE. PKCE is not strictly required of a
 * client that holds a secret, but it is what is recommended of every client
 * now: it ties the code to the exchange that asked for it, so a code stolen in
 * the redirect cannot be spent by anyone else.
 */

interface AuthorizationRequest {
  /** Ties the callback to the request that started it, against CSRF. */
  state: string;
  /** Ties the identity token to this sign-in, against replay. */
  nonce: string;
  /** The public half of the PKCE pair. */
  challenge: string;
}

/** What is asked of Entra, and why.
 *
 * `openid profile email` name the person; `offline_access` is what buys the
 * renewal token — without it the session would die after an hour and the
 * person would sign in again, all day long.
 */
const SCOPES = "openid profile email offline_access";

function tenant(): string {
  const id = process.env.AZURE_AD_TENANT_ID;
  if (!id) throw new Error("AZURE_AD_TENANT_ID est absent.");
  return id;
}

function clientId(): string {
  const id = process.env.AZURE_AD_CLIENT_ID;
  if (!id) throw new Error("AZURE_AD_CLIENT_ID est absent.");
  return id;
}

function redirectUri(): string {
  const uri = process.env.AZURE_AD_REDIRECT_URI;
  if (!uri) throw new Error("AZURE_AD_REDIRECT_URI est absent.");
  return uri;
}

function base64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

/** A random string, long enough that guessing it is out of the question. */
export function randomToken(): string {
  return base64url(crypto.getRandomValues(new Uint8Array(32)));
}

/**
 * The PKCE pair: a secret kept here, and the fingerprint sent to Entra.
 *
 * Entra keeps the fingerprint with the code it issues, and only gives a token
 * to whoever can show the secret behind it.
 */
export async function pkcePair(): Promise<{ verifier: string; challenge: string }> {
  const verifier = randomToken();
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(verifier),
  );
  return { verifier, challenge: base64url(new Uint8Array(digest)) };
}

/** Where the browser is sent to sign in. */
export async function authorizationUrl(request: AuthorizationRequest): Promise<string> {
  const url = new URL(
    `https://login.microsoftonline.com/${tenant()}/oauth2/v2.0/authorize`,
  );
  url.searchParams.set("client_id", clientId());
  url.searchParams.set("response_type", "code");
  url.searchParams.set("redirect_uri", redirectUri());
  url.searchParams.set("response_mode", "query");
  url.searchParams.set("scope", SCOPES);
  url.searchParams.set("state", request.state);
  url.searchParams.set("nonce", request.nonce);
  url.searchParams.set("code_challenge", request.challenge);
  url.searchParams.set("code_challenge_method", "S256");
  return url.toString();
}

/**
 * Whether an address belongs to the company.
 *
 * The tenant already limits who may sign in; this closes the door a second
 * time, on the guest accounts a tenant often carries.
 */
export function isAllowedEmail(email: string): boolean {
  const domain = (process.env.ALLOWED_EMAIL_DOMAIN ?? "waat.fr").toLowerCase();
  const address = email.trim().toLowerCase();
  // The whole domain, not a prefix of it: « @waat.fr.evil.com » ends elsewhere.
  return address.endsWith(`@${domain}`);
}

/**
 * How long before expiry a session is renewed.
 *
 * A request that leaves just before the token dies would arrive after: we take
 * a minute's lead rather than let a dead token through.
 */
const RENEW_AHEAD_SECONDS = 60;

export function needsRefresh(
  session: { expiresAt: number },
  now = Math.floor(Date.now() / 1000),
): boolean {
  return session.expiresAt - RENEW_AHEAD_SECONDS <= now;
}

/** What Entra answers when it hands over, or renews, a session. */
export interface TokenSet {
  idToken: string;
  refreshToken: string;
  /** Seconds since the epoch, computed from the lifetime Entra gives. */
  expiresAt: number;
}

function tokenEndpoint(): string {
  return `https://login.microsoftonline.com/${tenant()}/oauth2/v2.0/token`;
}

function clientSecret(): string {
  const secret = process.env.AZURE_AD_CLIENT_SECRET;
  if (!secret) throw new Error("AZURE_AD_CLIENT_SECRET est absent.");
  return secret;
}

async function askForTokens(body: URLSearchParams): Promise<TokenSet | null> {
  const response = await fetch(tokenEndpoint(), {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    cache: "no-store",
  });

  if (!response.ok) {
    // What Entra refuses, it explains — but its explanation is for us, not for
    // the person: it names the client and the tenant.
    console.error("[auth] Entra a refusé l'échange :", await response.text());
    return null;
  }

  const payload = (await response.json()) as {
    id_token?: string;
    refresh_token?: string;
    expires_in?: number;
  };
  if (!payload.id_token || !payload.refresh_token) return null;

  return {
    idToken: payload.id_token,
    refreshToken: payload.refresh_token,
    expiresAt: Math.floor(Date.now() / 1000) + (payload.expires_in ?? 3600),
  };
}

/** Trades the code the callback carries for a session. */
export async function exchangeCode(
  code: string,
  verifier: string,
): Promise<TokenSet | null> {
  return askForTokens(
    new URLSearchParams({
      client_id: clientId(),
      client_secret: clientSecret(),
      grant_type: "authorization_code",
      code,
      redirect_uri: redirectUri(),
      code_verifier: verifier,
      scope: SCOPES,
    }),
  );
}

/**
 * Buys a fresh session with the renewal token.
 *
 * Entra rotates them: what comes back carries a new renewal token, and the
 * old one dies. The session must therefore be written back every time —
 * keeping the previous one would lock the person out at the next renewal.
 */
export async function refreshTokens(refreshToken: string): Promise<TokenSet | null> {
  return askForTokens(
    new URLSearchParams({
      client_id: clientId(),
      client_secret: clientSecret(),
      grant_type: "refresh_token",
      refresh_token: refreshToken,
      scope: SCOPES,
    }),
  );
}

/** The address Entra put in the identity token, without verifying it.
 *
 * Reading is not trusting: the API checks the signature. Here it only serves
 * to name the person in the session and to close the door on other domains.
 */
export function emailFromIdToken(idToken: string): string | null {
  try {
    const [, payload] = idToken.split(".");
    const claims = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))) as {
      preferred_username?: string;
      email?: string;
      upn?: string;
    };
    return claims.preferred_username ?? claims.email ?? claims.upn ?? null;
  } catch {
    return null;
  }
}
