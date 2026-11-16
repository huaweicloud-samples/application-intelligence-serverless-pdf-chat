// Thin fetch-based API client.
//
// Every request carries:
//   - Content-Type: application/json
//   - X-User-Id: the per-browser user id, used to scope documents
//   - X-Apig-AppCode: only when APIG is configured with simple App authentication

import { API_ENDPOINT, APIG_APP_CODE, getUserId } from "./config";

function buildHeaders(): Record<string, string> {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
    "X-User-Id": getUserId(),
  };
  if (APIG_APP_CODE) {
    h["X-Apig-AppCode"] = APIG_APP_CODE;
  }
  return h;
}

function buildUrl(path: string): string {
  const base = API_ENDPOINT.replace(/\/$/, "");
  return base + (path.startsWith("/") ? path : "/" + path);
}

export async function apiGet<T = any>(
  path: string,
  queryParams?: Record<string, string>
): Promise<T> {
  let u = buildUrl(path);
  if (queryParams) {
    u += "?" + new URLSearchParams(queryParams).toString();
  }
  const resp = await fetch(u, { method: "GET", headers: buildHeaders() });
  if (!resp.ok) {
    throw new Error(`GET ${path} -> ${resp.status}`);
  }
  return (await resp.json()) as T;
}

export async function apiPost<T = any>(path: string, body?: any): Promise<T> {
  const resp = await fetch(buildUrl(path), {
    method: "POST",
    headers: buildHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    throw new Error(`POST ${path} -> ${resp.status}`);
  }
  return (await resp.json()) as T;
}

export async function apiDelete<T = any>(path: string): Promise<T> {
  const resp = await fetch(buildUrl(path), {
    method: "DELETE",
    headers: buildHeaders(),
  });
  if (!resp.ok) {
    throw new Error(`DELETE ${path} -> ${resp.status}`);
  }
  return (await resp.json()) as T;
}
