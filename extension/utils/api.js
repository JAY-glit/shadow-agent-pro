// utils/api.js — shared fetch wrapper for talking to the Flask backend.
// Handles JWT acquisition/storage so every scan request is authenticated.

const API_BASE = "http://localhost:5000/api";

async function getToken() {
  const { authToken } = await chrome.storage.local.get("authToken");
  if (authToken) return authToken;

  const { clientId } = await chrome.storage.local.get("clientId");
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId }),
  });
  const data = await res.json();
  await chrome.storage.local.set({ authToken: data.token, clientId: data.client_id });
  return data.token;
}

async function authedFetch(path, options = {}) {
  const token = await getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (res.status === 401) {
    // Token expired — clear and retry once with a fresh one
    await chrome.storage.local.remove("authToken");
    const freshToken = await getToken();
    return fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${freshToken}`,
        ...(options.headers || {}),
      },
    });
  }
  return res;
}

export async function scanUrl(url) {
  const res = await authedFetch("/scan/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(`Scan failed: ${res.status}`);
  return res.json(); // { verdict, confidence, reasons: [...] }
}

export async function scanContent(url, indicators) {
  const res = await authedFetch("/scan/content", {
    method: "POST",
    body: JSON.stringify({ url, indicators }),
  });
  return res.json();
}

export async function getThreats(limit = 50) {
  const res = await authedFetch(`/threats?limit=${limit}`);
  return res.json();
}

export async function getThreatById(id) {
  const res = await authedFetch(`/threats/${id}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getMaliciousDomains() {
  const res = await authedFetch("/threats/domains");
  const data = await res.json();
  return data.domains || [];
}

export async function getStats() {
  const res = await authedFetch("/stats");
  return res.json();
}
