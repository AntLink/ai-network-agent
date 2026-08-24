export async function requestJson(url, init) {
    const res = await fetch(url, init);
    if (!res.ok)
        throw new Error(`HTTP ${res.status}`);
    return res.json();
}
