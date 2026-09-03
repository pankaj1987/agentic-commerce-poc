// frontend/src/utils/sessionStorage.js

const SESSION_STORAGE_KEY =
  "agentic_commerce_session_id";


/**
 * Return the current public commerce session ID.
 *
 * The browser must never store:
 * - Shopify cart_id
 * - LangGraph thread_id
 */
export function getCommerceSessionId() {
  const sessionId =
    localStorage.getItem(
      SESSION_STORAGE_KEY
    );

  if (!sessionId) {
    return null;
  }

  const normalized =
    sessionId.trim();

  return normalized || null;
}


/**
 * Persist the public commerce session returned by the backend.
 */
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


/**
 * Remove the current browser-side conversation identity.
 */
export function clearCommerceSessionId() {
  localStorage.removeItem(
    SESSION_STORAGE_KEY
  );
}


/**
 * Return whether a conversation session currently exists.
 */
export function hasCommerceSession() {
  return Boolean(
    getCommerceSessionId()
  );
}