/**
 * Typed client for the Studio API.
 *
 * The browser never holds an OpenAI key. Every model call happens server-side, so
 * this module only ever talks to our own FastAPI service on the same origin.
 */

export interface HealthResponse {
  status: string;
  version: string;
}

export class ApiError extends Error {
  /** HTTP status, or 0 when the request never reached the service. */
  readonly status: number;

  constructor(status: number, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ApiError";
    this.status = status;
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      headers: { Accept: "application/json" },
      ...(signal ? { signal } : {}),
    });
  } catch (cause) {
    throw new ApiError(0, "The Studio service could not be reached.", { cause });
  }

  if (!response.ok) {
    throw new ApiError(response.status, `The Studio service returned ${String(response.status)}.`);
  }

  return (await response.json()) as T;
}

/** Liveness only: this tells you the process is up, not that it is ready to work. */
export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health", signal);
}
