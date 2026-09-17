/**
 * BFF : unique porte d'entree du navigateur vers l'API.
 *
 * Le navigateur appelle `/api/v1/...`, ce handler relaie vers
 * `${API_URL}/api/v1/...` en injectant le jeton Entra recupere cote serveur.
 * Le jeton ne traverse jamais la frontiere du navigateur.
 *
 * Les chemins sont identiques des deux cotes : un seul vocabulaire d'URL.
 */
import { NextRequest, NextResponse } from "next/server";

import { getAccessToken } from "@/lib/auth/session";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const API_PREFIX = process.env.API_PREFIX ?? "/api/v1";

const HOP_BY_HOP = new Set(["connection", "keep-alive", "transfer-encoding", "host"]);

async function proxy(request: NextRequest): Promise<NextResponse> {
  const incoming = new URL(request.url);
  const suffix = incoming.pathname.replace(/^\/api\/v1/, "");
  const target = `${API_URL}${API_PREFIX}${suffix}${incoming.search}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) headers.set(key, value);
  });

  const token = await getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const hasBody = !["GET", "HEAD"].includes(request.method);

  const response = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.text() : undefined,
    cache: "no-store",
  });

  const payload = await response.text();

  return new NextResponse(payload || null, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
