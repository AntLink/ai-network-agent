const API_BASE = process.env.NETWORK_AGENT_API || "http://localhost:8000/api/v1";
export async function apiGet(path) {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url);
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json();
}
export async function apiPost(path, body) {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json();
}
