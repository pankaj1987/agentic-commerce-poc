import { useState } from "react";

import { sendChatMessage } from "../api/chatApi";

import {
  clearCommerceSessionId,
  getCommerceSessionId,
  hasCommerceSession,
  saveCommerceSessionId,
} from "../utils/sessionStorage";


function ChatWindow({
  onCartChanged,
  onNewConversation,
}) {
  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [resetting, setResetting] =
    useState(false);

  const [sessionActive, setSessionActive] =
    useState(() => hasCommerceSession());


  const appendMessage = (message) => {
    setMessages((currentMessages) => [
      ...currentMessages,
      message,
    ]);
  };


  const isInvalidSessionError = (
    requestError
  ) => {
    const status =
      requestError?.response?.status;

    const detail = String(
      requestError?.response?.data?.detail || ""
    ).toLowerCase();

    return (
      [400, 404, 410].includes(status) &&
      (
        detail.includes("session") &&
        (
          detail.includes("does not exist") ||
          detail.includes("not active") ||
          detail.includes("expired") ||
          detail.includes("not found")
        )
      )
    );
  };


  const executeChatRequest = (
    userMessage,
    sessionId
  ) => {
    return sendChatMessage(
      userMessage,
      sessionId
    );
  };


  const handleSendMessage = async () => {
    const userMessage = input.trim();

    if (
      !userMessage ||
      loading ||
      resetting
    ) {
      return;
    }

    appendMessage({
      role: "user",
      content: userMessage,
    });

    setInput("");
    setLoading(true);

    try {
      let sessionId =
        getCommerceSessionId();

      let result;

      try {
        result = await executeChatRequest(
          userMessage,
          sessionId
        );
      } catch (requestError) {
        // Retry once only when session lookup itself is stale/invalid.
        if (
          sessionId &&
          isInvalidSessionError(requestError)
        ) {
          clearCommerceSessionId();
          setSessionActive(false);

          let newSessionId = null;

          if (
            typeof onNewConversation ===
            "function"
          ) {
            newSessionId =
              await onNewConversation();
          }

          result = await executeChatRequest(
            userMessage,
            newSessionId
          );
        } else {
          throw requestError;
        }
      }

      if (result.session_id) {
        saveCommerceSessionId(
          result.session_id
        );
        setSessionActive(true);
      }

      appendMessage({
        role: "assistant",
        content:
          result.response ||
          "No response was returned.",
      });

      if (
        result.cart_changed &&
        typeof onCartChanged === "function"
      ) {
        await onCartChanged();
      }
    } catch (requestError) {
      console.error(
        "Chat request failed:",
        requestError
      );

      const errorMessage =
        requestError?.response?.data?.detail ||
        requestError?.message ||
        "Unable to process your request.";

      appendMessage({
        role: "assistant",
        content:
          "Sorry, I could not process that request. " +
          errorMessage,
        error: true,
      });
    } finally {
      setLoading(false);
    }
  };


  const handleNewConversation = async () => {
    if (loading || resetting) {
      return;
    }

    setResetting(true);

    try {
      clearCommerceSessionId();
      setSessionActive(false);
      setMessages([]);
      setInput("");

      if (
        typeof onNewConversation ===
        "function"
      ) {
        const newSessionId =
          await onNewConversation();

        if (newSessionId) {
          saveCommerceSessionId(
            newSessionId
          );
          setSessionActive(true);
        }
      }
    } catch (error) {
      console.error(
        "Unable to start new conversation:",
        error
      );

      appendMessage({
        role: "assistant",
        content:
          "Unable to start a new conversation.",
        error: true,
      });
    } finally {
      setResetting(false);
    }
  };


  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleSendMessage();
    }
  };


  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div>
          <h2>AI Commerce Assistant</h2>
          <div className="chat-session-status">
            {sessionActive
              ? "Conversation active"
              : "New conversation"}
          </div>
        </div>

        <button
          type="button"
          className="new-chat-button"
          onClick={handleNewConversation}
          disabled={loading || resetting}
        >
          {resetting
            ? "Starting..."
            : "New conversation"}
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty-state">
            Ask about products, inventory,
            product benefits, policies,
            promotions, or your shopping cart.
          </div>
        )}

        {messages.map((message, index) => {
          const isUser =
            message.role === "user";

          return (
            <div
              key={`${message.role}-${index}`}
              className={[
                "message",
                isUser
                  ? "user-message"
                  : "assistant-message",
                message.error
                  ? "message-error"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="message-role">
                {isUser ? "You" : "Assistant"}
              </div>

              <div>{message.content}</div>
            </div>
          );
        })}

        {loading && (
          <div className="message assistant-message">
            <div className="message-role">
              Assistant
            </div>
            <div>Thinking...</div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <textarea
          value={input}
          placeholder="Ask about products, inventory, policies, or your cart..."
          onChange={(event) =>
            setInput(event.target.value)
          }
          onKeyDown={handleKeyDown}
          disabled={loading || resetting}
          rows={3}
        />

        <button
          type="button"
          onClick={handleSendMessage}
          disabled={
            loading ||
            resetting ||
            !input.trim()
          }
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}


export default ChatWindow;
