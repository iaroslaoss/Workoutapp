import { useAuth } from "../lib/auth";
import { api } from "../lib/api";

export function useApi() {
  const { token } = useAuth();

  return {
    get: <T,>(path: string) => api<T>(path, { method: "GET" }, token || undefined),
    post: <T,>(path: string, body: unknown) =>
      api<T>(path, { method: "POST", body: JSON.stringify(body) }, token || undefined),
    put: <T,>(path: string, body: unknown) =>
      api<T>(path, { method: "PUT", body: JSON.stringify(body) }, token || undefined),
    del: <T,>(path: string) => api<T>(path, { method: "DELETE" }, token || undefined),
  };
}
