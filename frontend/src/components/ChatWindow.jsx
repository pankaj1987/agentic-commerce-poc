// frontend/src/components/ChatWindow.jsx

import {
  useState,
} from "react";

import {
  sendChatMessage,
} from "../api/chatApi";

import {
  clearCommerceSessionId,
  getCommerceSessionId,
  hasCommerceSession,
  saveCommerceSessionId,
} from "../utils/sessionStorage";


function ChatWindow({
  onCartChanged,
}) {
  // ============================================================
  // COMPONENT STATE
  // ============================================================

  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [
    sessionActive,
    setSessionActive,
  ] = useState(
    () => hasCommerceSession()
  );


  // ============================================================
  // ADD MESSAGE TO UI
  // ============================================================

  const appendMessage = (
    message
  ) => {
    setMessages(
      (currentMessages) => [
        ...currentMessages,
        message,
      ]
    );
  };


  // ============================================================
  // CHECK FOR INVALID / EXPIRED SESSION
  // ============================================================

  const isInvalidSessionError = (
    requestError
  ) => {
    const status =
      requestError?.response?.status;

    const detail =
      String(
        requestError?.response
          ?.data?.detail || ""
      ).toLowerCase();

    if (status !== 400) {
      return false;
    }

    return (
      detail.includes(
        "session does not exist"
      ) ||
      detail.includes(
        "session is not active"
      ) ||
      detail.includes(
        "session has expired"
      )
    );
  };


  // ============================================================
  // EXECUTE CHAT REQUEST
  // ============================================================

  const executeChatRequest = async (
    userMessage,
    sessionId
  ) => {
    return sendChatMessage(
      userMessage,
      sessionId
    );
  };


  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const handleSendMessage =
    async () => {
      const userMessage =
        input.trim();

      if (!userMessage) {
        return;
      }

      if (loading) {
        return;
      }

      // --------------------------------------------------------
      // DISPLAY USER MESSAGE
      // --------------------------------------------------------

      appendMessage({
        role: "user",
        content: userMessage,
      });

      setInput("");

      setError("");

      setLoading(true);

      try {
        // ------------------------------------------------------
        // GET CURRENT APPLICATION SESSION
        // ------------------------------------------------------

        let sessionId =
          getCommerceSessionId();

        let result;

        try {
          // ----------------------------------------------------
          // NORMAL REQUEST
          // ----------------------------------------------------

          result =
            await executeChatRequest(
              userMessage,
              sessionId
            );

        } catch (requestError) {
          // ----------------------------------------------------
          // STALE / INVALID SESSION RECOVERY
          // ----------------------------------------------------
          //
          // If the stored session no longer exists,
          // clear the stale browser session and retry once.
          //
          // Session lookup fails before graph execution, so this
          // recovery does not re-execute a successfully completed
          // commerce mutation.
          //

          if (
            sessionId &&
            isInvalidSessionError(
              requestError
            )
          ) {
            console.warn(
              "Stored commerce session is invalid. " +
              "Starting a new session."
            );

            clearCommerceSessionId();

            setSessionActive(
              false
            );

            sessionId = null;

            result =
              await executeChatRequest(
                userMessage,
                null
              );

          } else {
            throw requestError;
          }
        }


        // ------------------------------------------------------
        // SAVE SESSION RETURNED BY BACKEND
        // ------------------------------------------------------

        if (result.session_id) {
          saveCommerceSessionId(
            result.session_id
          );

          setSessionActive(
            true
          );
        }


        // ------------------------------------------------------
        // DISPLAY ASSISTANT MESSAGE
        // ------------------------------------------------------

        appendMessage({
          role: "assistant",

          content:
            result.response ||
            "No response was returned.",
        });


        // ------------------------------------------------------
        // REFRESH CART AFTER CHAT MUTATION
        // ------------------------------------------------------
        //
        // Step 19 backend lifecycle may create/update the Shopify
        // cart without exposing the cart ID to this component.
        //

        if (
          result.cart_changed &&
          typeof onCartChanged ===
            "function"
        ) {
          try {
            await onCartChanged();
          } catch (
            cartRefreshError
          ) {
            console.error(
              "Unable to refresh cart:",
              cartRefreshError
            );
          }
        }

      } catch (requestError) {
        console.error(
          "Chat request failed:",
          requestError
        );

        const errorMessage =
          requestError?.response
            ?.data?.detail ||
          requestError?.message ||
          "Unable to process your request.";

        setError(
          errorMessage
        );

        appendMessage({
          role: "assistant",

          content:
            `Sorry, I could not process that request. ` +
            `${errorMessage}`,

          error: true,
        });

      } finally {
        setLoading(
          false
        );
      }
    };


  // ============================================================
  // NEW CONVERSATION
  // ============================================================

  const handleNewConversation =
    () => {
      if (loading) {
        return;
      }

      // Remove only the public session ID.
      //
      // We deliberately do NOT know or clear:
      // - LangGraph thread_id
      // - Shopify cart_id
      //
      // Backend session retention can be handled independently.
      clearCommerceSessionId();

      setSessionActive(
        false
      );

      setMessages([]);

      setInput("");

      setError("");
    };


  // ============================================================
  // KEYBOARD HANDLER
  // ============================================================

  const handleKeyDown = (
    event
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      handleSendMessage();
    }
  };


  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="chat-window">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <div className="chat-header">

        <div>
          <h2>
            AI Commerce Assistant
          </h2>

          <div className="chat-session-status">
            {sessionActive
              ? "Conversation active"
              : "New conversation"}
          </div>
        </div>


        <button
          type="button"
          className="new-chat-button"
          onClick={
            handleNewConversation
          }
          disabled={
            loading
          }
        >
          New conversation
        </button>

      </div>


      {/* ======================================================
          MESSAGE AREA
          ====================================================== */}

      <div className="chat-messages">

        {messages.length === 0 && (
          <div className="chat-empty-state">

            <div>
              Ask me about:
            </div>

            <div>
              Products, inventory,
              product benefits,
              policies, promotions,
              and your shopping cart.
            </div>

          </div>
        )}


        {messages.map(
          (
            message,
            index
          ) => {
            const isUser =
              message.role ===
              "user";

            return (
              <div
                key={
                  `${message.role}-${index}`
                }
                className={
                  [
                    "chat-message",

                    isUser
                      ? "user"
                      : "assistant",

                    message.error
                      ? "error"
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" ")
                }
              >

                <div className="chat-message-role">
                  {isUser
                    ? "You"
                    : "Assistant"}
                </div>


                <div className="chat-message-content">
                  {message.content}
                </div>

              </div>
            );
          }
        )}


        {/* ====================================================
            LOADING INDICATOR
            ==================================================== */}

        {loading && (
          <div
            className={
              "chat-message assistant"
            }
          >
            <div className="chat-message-role">
              Assistant
            </div>

            <div className="chat-message-content">
              Thinking...
            </div>
          </div>
        )}

      </div>


      {/* ======================================================
          ERROR
          ====================================================== */}

      {error && (
        <div
          className="chat-error"
          role="alert"
        >
          {error}
        </div>
      )}


      {/* ======================================================
          INPUT
          ====================================================== */}

      <div className="chat-input-container">

        <textarea
          value={input}
          placeholder={
            "Ask about products, inventory, policies, or your cart..."
          }
          onChange={
            (event) =>
              setInput(
                event.target.value
              )
          }
          onKeyDown={
            handleKeyDown
          }
          disabled={
            loading
          }
          rows={3}
        />


        <button
          type="button"
          onClick={
            handleSendMessage
          }
          disabled={
            loading ||
            !input.trim()
          }
        >
          {loading
            ? "Sending..."
            : "Send"}
        </button>

      </div>

    </div>
  );
}


export default ChatWindow;