export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
export const BACKEND_BASE_URL = process.env.API_BASE_URL || "http://127.0.0.1:8000";

type ApiFetchInit = RequestInit & {
  ttlMs?: number;
  force?: boolean;
};

const GET_CACHE = new Map<string, { expiresAt: number; data: unknown }>();
const INFLIGHT_GETS = new Map<string, Promise<unknown>>();

export async function apiFetch<T>(path: string, init?: ApiFetchInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  const isGet = method === "GET" && !init?.body;
  const ttlMs = init?.ttlMs ?? 12000;
  const cacheKey = `${method}:${path}`;
  const now = Date.now();

  if (isGet && !init?.force) {
    const cached = GET_CACHE.get(cacheKey);
    if (cached && cached.expiresAt > now) {
      return cached.data as T;
    }
    const inflight = INFLIGHT_GETS.get(cacheKey);
    if (inflight) {
      return inflight as Promise<T>;
    }
  }

  const requestPromise = fetch(`${API_BASE_URL}${path}`, {
    ...init,
    method,
    credentials: "include",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  }).then(async (response) => {
    if (!response.ok) {
      let message = `Request failed: ${response.status}`;
      const raw = await response.text();
      if (raw) {
        try {
          const payload = JSON.parse(raw) as { detail?: string };
          if (payload?.detail) {
            message = payload.detail;
          } else {
            message = raw;
          }
        } catch {
          message = raw;
        }
      }

      throw new Error(message);
    }

    const data = (await response.json()) as T;
    if (isGet) {
      GET_CACHE.set(cacheKey, {
        expiresAt: Date.now() + ttlMs,
        data,
      });
    } else {
      GET_CACHE.clear();
    }
    return data;
  });

  if (isGet) {
    INFLIGHT_GETS.set(cacheKey, requestPromise as Promise<unknown>);
    try {
      return await requestPromise;
    } finally {
      INFLIGHT_GETS.delete(cacheKey);
    }
  }

  try {
    return await requestPromise;
  } finally {
    if (!isGet) {
      INFLIGHT_GETS.clear();
    }
  }
}

export function clearApiCache() {
  GET_CACHE.clear();
  INFLIGHT_GETS.clear();
}
