import { useState } from "react";

import {
  sendChatMessage,
} from "../api/chatApi";


function ChatWindow({
  cartId,
  onCartChanged,
}) {
  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  // ============================================================
  // SEND CHAT MESSAGE
  // ============================================================

  const sendMessage = async () => {
    const message =
      input.trim();

    if (!message || loading) {
      return;
    }

    // Add user message immediately.
    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: message,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      // ---------------------------------------------------------
      // Send request to FastAPI /api/chat
      // ---------------------------------------------------------

      const result =
        await sendChatMessage(
          message,
          cartId
        );


      // ---------------------------------------------------------
      // Add AI response to chat
      // ---------------------------------------------------------

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: result.response,
        },
      ]);


      // ---------------------------------------------------------
      // Refresh cart after successful chat request.
      //
      // The Cart Agent may have changed Shopify cart state through:
      //
      // - add_to_cart
      // - update_quantity
      // - remove_from_cart
      // - apply_promotion
      //
      // React does not automatically know that Shopify changed,
      // so retrieve the latest cart and update CommercePage state.
      // ---------------------------------------------------------

      if (
        result.cart_changed &&
        onCartChanged
      ) {
        try {
          await onCartChanged();
        } catch (cartRefreshError) {
          console.error(
            "Unable to refresh cart after chat operation:",
            cartRefreshError
          );
        }
      }

    } catch (error) {
      console.error(
        "Chat error:",
        error
      );


      // ---------------------------------------------------------
      // Display API error when available
      // ---------------------------------------------------------

      const errorMessage =
        error.response?.data?.detail ||
        "Unable to process the request.";


      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: errorMessage,
        },
      ]);

    } finally {
      setLoading(false);
    }
  };


  // ============================================================
  // ENTER KEY HANDLER
  // ============================================================

  const handleKeyDown = (
    event
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      sendMessage();
    }
  };


  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="chat-panel">

      <h2>
        AI Commerce Assistant
      </h2>


      <div className="chat-messages">

        {messages.length === 0 && (
          <div className="chat-welcome">
            Ask me about products,
            benefits, promotions or your
            shopping cart.
          </div>
        )}


        {messages.map(
          (message, index) => (
            <div
              key={index}
              className={
                message.role === "user"
                  ? "message user-message"
                  : "message assistant-message"
              }
            >
              {message.content}
            </div>
          )
        )}


        {loading && (
          <div className="message assistant-message">
            Thinking...
          </div>
        )}

      </div>


      <div className="chat-input">

        <textarea
          value={input}
          placeholder="Ask the AI commerce assistant..."
          onChange={(event) =>
            setInput(
              event.target.value
            )
          }
          onKeyDown={
            handleKeyDown
          }
          disabled={loading}
        />


        <button
          onClick={
            sendMessage
          }
          disabled={
            loading ||
            !input.trim()
          }
        >
          {loading
            ? "Processing..."
            : "Send"}
        </button>

      </div>

    </div>
  );
}

export default ChatWindow;