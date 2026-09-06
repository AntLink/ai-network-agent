const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1";

function baseUrl() {
  const fromProcess =
    globalThis.process?.env.AI_NETWORK_AGENT_API_BASE_URL || globalThis.process?.env.VITE_API_BASE_URL || "";
  const fromImportMeta =
    typeof import.meta !== "undefined" ? import.meta.env?.VITE_API_BASE_URL : "";
  return String(fromProcess || fromImportMeta || DEFAULT_BASE_URL).replace(/\/+$/, "");
}

function normalizePath(path) {
  const value = String(path || "");
  if (/^https?:\/\//i.test(value)) return value;
  if (value.startsWith("/api/v1/")) return `${baseUrl().replace(/\/api\/v1$/, "")}${value}`;
  return `${baseUrl()}${value.startsWith("/") ? value : `/${value}`}`;
}

async function request(method, path, body) {
  const response = await globalThis.fetch(normalizePath(path), {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
  }

  if (!response.ok) {
    const message = data?.detail || data?.message || data?.error?.message || response.statusText;
    throw new Error(`API ${method} ${path} failed: ${response.status} ${message}`);
  }

  return data;
}

export function apiGet(path) {
  return request("GET", path);
}

export function apiPost(path, body) {
  return request("POST", path, body);
}
