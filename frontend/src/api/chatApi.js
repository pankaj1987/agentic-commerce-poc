// frontend/src/api/chatApi.js

import apiClient from "./apiClient";


/**
 * Send one customer conversation turn.
 *
 * Public request:
 *
 * {
 *   message: "...",
 *   session_id: "..." | null
 * }
 *
 * The browser must NOT send:
 * - cart_id
 * - thread_id
 */
export const sendChatMessage = async (
  message,
  sessionId = null
) => {
  const normalizedMessage =
    message?.trim();

  if (!normalizedMessage) {
    throw new Error(
      "Message cannot be empty."
    );
  }

  const response =
    await apiClient.post(
      "/api/chat",
      {
        message:
          normalizedMessage,

        session_id:
          sessionId || null,
      }
    );

  return response.data;
};