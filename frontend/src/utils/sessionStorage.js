// frontend/src/utils/sessionStorage.js

const SESSION_STORAGE_KEY =
  "agentic_commerce_session_id";

const LEGACY_CART_STORAGE_KEY =
  "shopify_cart_id";


export function getCommerceSessionId() {
  const sessionId = localStorage.getItem(
    SESSION_STORAGE_KEY
  );

  if (!sessionId) {
    return null;
  }

  const normalized = sessionId.trim();
  return normalized || null;
}


export function saveCommerceSessionId(
  sessionId
) {
  if (!sessionId) {
    return;
  }

  const normalized =
    String(sessionId).trim();

  if (!normalized) {
    return;
  }

  localStorage.setItem(
    SESSION_STORAGE_KEY,
    normalized
  );
}


export function clearCommerceSessionId() {
  localStorage.removeItem(
    SESSION_STORAGE_KEY
  );
}


export function hasCommerceSession() {
  return Boolean(
    getCommerceSessionId()
  );
}


// One-time migration helper for browsers that ran the Phase 2 UI.
// Phase 3 never persists the Shopify cart ID in browser storage.
export function clearLegacyCartStorage() {
  localStorage.removeItem(
    LEGACY_CART_STORAGE_KEY
  );
}
