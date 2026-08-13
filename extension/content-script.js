// content-script.js
// Scans the live DOM for phishing indicators: fake login forms, brand
// impersonation, hidden iframes, and injects a MutationObserver to catch
// forms added dynamically after initial page load (a common evasion trick).

function scanForCredentialForms() {
  const forms = Array.from(document.querySelectorAll("form"));
  return forms
    .filter((f) => f.querySelector('input[type="password"]'))
    .map((f) => ({
      action: f.action || "(none)",
      crossOrigin: f.action && new URL(f.action, location.href).origin !== location.origin,
    }));
}

function scanForHiddenIframes() {
  return Array.from(document.querySelectorAll("iframe"))
    .filter((f) => {
      const style = window.getComputedStyle(f);
      return (
        style.display === "none" ||
        style.visibility === "hidden" ||
        parseInt(style.width) <= 1 ||
        parseInt(style.height) <= 1
      );
    })
    .map((f) => f.src);
}

function scanForBrandImpersonation() {
  const brands = ["paypal", "google", "microsoft", "apple", "amazon", "netflix", "bankofamerica"];
  const host = location.hostname.toLowerCase();
  return brands.filter((b) => host.includes(b) && !host.endsWith(`${b}.com`));
}

function scanForUrgencyLanguage() {
  const urgentPhrases = ["verify your account", "act now", "suspended", "confirm your identity", "urgent action required"];
  const text = document.body?.innerText?.toLowerCase() || "";
  return urgentPhrases.filter((p) => text.includes(p));
}

function runFullScan() {
  const indicators = {
    credentialForms: scanForCredentialForms(),
    hiddenIframes: scanForHiddenIframes(),
    brandImpersonation: scanForBrandImpersonation(),
    urgencyLanguage: scanForUrgencyLanguage(),
  };

  const hasSignal =
    indicators.credentialForms.some((f) => f.crossOrigin) ||
    indicators.hiddenIframes.length > 0 ||
    indicators.brandImpersonation.length > 0 ||
    indicators.urgencyLanguage.length > 0;

  if (hasSignal) {
    chrome.runtime.sendMessage({ type: "CONTENT_SCAN_RESULT", indicators });
  }
}

// Initial scan once DOM is ready
runFullScan();

// Catch forms/iframes injected after load (evasion technique)
const observer = new MutationObserver((mutations) => {
  const relevant = mutations.some((m) =>
    Array.from(m.addedNodes).some(
      (n) => n.nodeName === "FORM" || n.nodeName === "IFRAME" || n.querySelector?.("form, iframe")
    )
  );
  if (relevant) runFullScan();
});

observer.observe(document.body, { childList: true, subtree: true });
