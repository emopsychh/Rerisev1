import { ApiError, type ApiErrorBody } from "./types";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./session";

const DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1";

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL).replace(/\/$/, "");
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
  headers?: Record<string, string>;
  retry?: boolean;
};

let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const access = json?.data?.access_token as string | undefined;
    if (!access) {
      clearTokens();
      return false;
    }
    setTokens(access, refresh);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = "GET",
    body,
    auth = true,
    headers = {},
    retry = true,
  } = options;

  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const reqHeaders: Record<string, string> = {
    Accept: "application/json",
    ...headers,
  };
  if (body !== undefined) {
    reqHeaders["Content-Type"] = "application/json";
  }
  if (auth) {
    const token = getAccessToken();
    if (token) reqHeaders.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method,
    headers: reqHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (response.status === 401 && auth && retry) {
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }
    const ok = await refreshPromise;
    if (ok) {
      return apiRequest<T>(path, { ...options, retry: false });
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const json = await response.json().catch(() => ({}));
  if (!response.ok) {
    const err = (json?.error || {
      code: "HTTP_ERROR",
      message: `HTTP ${response.status}`,
    }) as ApiErrorBody;
    throw new ApiError(response.status, err);
  }

  return (json?.data !== undefined ? json.data : json) as T;
}
