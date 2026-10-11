export type Params = Record<
  string,
  string | number | boolean | Array<string | number> | null | undefined
>;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** Fired when the server says the session is gone, so the app can show the login page. */
export const SESSION_EXPIRED = "session-expired";

export function toQuery(params: Params = {}): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "" || value === false) continue;
    if (Array.isArray(value)) value.forEach((v) => search.append(key, String(v)));
    else search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export async function api<T>(
  path: string,
  options: { params?: Params; method?: string; body?: unknown } = {},
): Promise<T> {
  const response = await fetch(`/api${path}${toQuery(options.params)}`, {
    method: options.method ?? "GET",
    headers: options.body === undefined ? undefined : { "Content-Type": "application/json" },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: "same-origin",
  });
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/")) {
      window.dispatchEvent(new Event(SESSION_EXPIRED));
    }
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // not JSON; keep the status text
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}
