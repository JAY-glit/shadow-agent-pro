// service-worker.js
// Intercepts navigation events, sends URLs to the Flask API for scoring,
// proactively syncs a local blocklist of confirmed-malicious domains so
// repeat offenders are blocked instantly (no round-trip needed), and
// dynamically injects declarativeNetRequest block rules for new threats.

import { scanUrl, scanContent, getMaliciousDomains } from "./utils/api.js";

let DYNAMIC_RULE_ID = 1000; // ad-hoc, per-navigation block rules
const BLOCKLIST_RULE_BASE = 2000; // synced blocklist rules use a separate ID range

// --- Keep-alive + periodic blocklist sync ------------------------------

chrome.alarms.create("keepAlive", { periodInMinutes: 0.4 });
chrome.alarms.create("blocklistSync", { periodInMinutes: 5 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepAlive") {
    chrome.storage.local.get("lastPing", () => {});
  }
  if (alarm.name === "blocklistSync") {
    syncBlocklist();
  }
});

chrome.runtime.onInstalled.addListener(syncBlocklist);
chrome.runtime.onStartup.addListener(syncBlocklist);

async function syncBlocklist() {
  try {
    const domains = await getMaliciousDomains();
    const existing = await chrome.declarativeNetRequest.getDynamicRules();
    const removeRuleIds = existing
      .filter((r) => r.id >= BLOCKLIST_RULE_BASE)
      .map((r) => r.id);

    const addRules = domains.slice(0, 4900).map((domain, i) => ({
      id: BLOCKLIST_RULE_BASE + i,
      priority: 1,
      action: { type: "block" },
      condition: { urlFilter: `||${domain}`, resourceTypes: ["main_frame"] },
    }));

    await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds, addRules });
    await chrome.storage.local.set({ blocklistSyncedAt: Date.now(), blocklistSize: addRules.length });
  } catch (err) {
    console.error("[ShadowAgent] blocklist sync failed:", err);
  }
}

// --- Live navigation scanning -------------------------------------------

chrome.webNavigation.onCompleted.addListener(async (details) => {
  if (details.frameId !== 0) return; // top-level frame navigations only

  const { url, tabId } = details;
  if (!url.startsWith("http")) return;

  try {
    // Fast path: local heuristic verdict, returned in well under a second.
    // deep_scan_pending tells us a Celery task is refining this in the
    // background; the popup listens for the follow-up via storage updates
    // pushed from a lightweight poll (kept simple — no socket in the SW).
    const result = await scanUrl(url);
    await chrome.storage.local.set({ [`scan:${tabId}`]: result });
    updateBadge(tabId, result.verdict);

    if (result.verdict === "malicious") {
      await blockUrl(url);
      notify(url);
    }

    if (result.deep_scan_pending && result.threat_id) {
      pollForDeepScanUpdate(tabId, result.threat_id, result);
    }
  } catch (err) {
    console.error("[ShadowAgent] scan failed:", err);
  }
});

// Short-lived poll (max ~10s) for the Celery deep-scan result to land.
// A full socket client isn't worth the bundle weight inside a service
// worker; this gives near-real-time refinement without one.
async function pollForDeepScanUpdate(tabId, threatId, previousResult) {
  const maxAttempts = 5;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise((r) => setTimeout(r, 2000));
    try {
      const { getThreatById } = await import("./utils/api.js");
      const updated = await getThreatById(threatId);
      if (!updated || updated.verdict === previousResult.verdict) continue;

      await chrome.storage.local.set({ [`scan:${tabId}`]: { ...previousResult, ...updated } });
      updateBadge(tabId, updated.verdict);

      if (updated.verdict === "malicious" && previousResult.verdict !== "malicious") {
        await blockUrl(updated.url);
        notify(updated.url);
      }
      return;
    } catch {
      // API unreachable this round — just try again next tick
    }
  }
}

function notify(url) {
  chrome.notifications?.create({
    type: "basic",
    iconUrl: "icons/icon48.png",
    title: "Shadow Agent Pro — Threat Blocked",
    message: `Blocked malicious site: ${new URL(url).hostname}`,
  });
}

function updateBadge(tabId, verdict) {
  const colors = { malicious: "#e53935", suspicious: "#fb8c00", safe: "#43a047" };
  const text = { malicious: "!", suspicious: "?", safe: "" };
  chrome.action.setBadgeBackgroundColor({ tabId, color: colors[verdict] || "#9e9e9e" });
  chrome.action.setBadgeText({ tabId, text: text[verdict] ?? "" });
}

async function blockUrl(url) {
  const hostname = new URL(url).hostname;
  const ruleId = DYNAMIC_RULE_ID++;

  await chrome.declarativeNetRequest.updateDynamicRules({
    addRules: [
      {
        id: ruleId,
        priority: 1,
        action: { type: "block" },
        condition: { urlFilter: `||${hostname}`, resourceTypes: ["main_frame"] },
      },
    ],
    removeRuleIds: [],
  });
}

// --- Content-script relay -------------------------------------------------

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "CONTENT_SCAN_RESULT") {
    scanContent(sender.tab?.url, message.indicators)
      .then((data) => sendResponse(data))
      .catch((err) => sendResponse({ error: String(err) }));
    return true; // keep channel open for async response
  }
});
