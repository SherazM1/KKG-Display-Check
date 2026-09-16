import "server-only";

export interface HealthResponse {
  status: "ok";
}

export interface DisplayFamily {
  id: string;
  label: string;
  configurations: {
    id: string;
    label: string;
    baselines: { id: string; label: string; footprint_id: string }[];
  }[];
}

export interface DisplaysResponse {
  families: DisplayFamily[];
}

type ApiResult<T> = { ok: true; data: T } | { ok: false };

// Only these read-only endpoints are exposed to presentation components.
interface Responses {
  "/api/health": HealthResponse;
  "/api/displays": DisplaysResponse;
}

async function get<K extends keyof Responses>(path: K): Promise<ApiResult<Responses[K]>> {
  try {
    const origin = process.env.DISPLAY_CHECK_API_URL ?? "http://127.0.0.1:8000";
    const response = await fetch(new URL(path, origin), {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return { ok: false };
    return { ok: true, data: (await response.json()) as Responses[K] };
  } catch {
    // Never expose server addresses, errors, or credentials in rendered output.
    return { ok: false };
  }
}

export const getHealth = () => get("/api/health");
export const getDisplays = () => get("/api/displays");
