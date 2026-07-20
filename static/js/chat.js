// Chat Functions

const chatList = document.getElementById("chat-list");
const chatWindow = document.getElementById("chat-window");
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const newChatButton = document.getElementById("new-chat-btn");

let isSending = false;

function autoResizeTextarea() {
  if (!messageInput) return;
  messageInput.style.height = "auto";
  messageInput.style.height = `${messageInput.scrollHeight}px`;
}

function scrollToBottom() {
  if (!chatWindow) return;
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

function appendMessage(role, content) {
  if (!chatWindow) return;

  const wrapper = document.createElement("div");
  wrapper.className = role === "user" ? "user-container" : "ai-container";

  const message = document.createElement("div");
  message.className = role === "user" ? "user-message" : "ai-message";
  message.innerHTML = escapeHtml(content);

  wrapper.appendChild(message);
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

async function sendMessage(text) {
  if (isSending || !text) return;
  isSending = true;

  appendMessage("user", text);
  messageInput.value = "";
  autoResizeTextarea();

  try {
    const response = await fetch("/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!response.ok) {
      appendMessage("assistant", "Server error. Please try again.");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let result = "";
    let done = false;

    const assistantWrapper = document.createElement("div");
    assistantWrapper.className = "ai-container";
    const assistantMessage = document.createElement("div");
    assistantMessage.className = "ai-message";
    assistantMessage.textContent = "Typing...";
    assistantWrapper.appendChild(assistantMessage);
    chatWindow.appendChild(assistantWrapper);
    scrollToBottom();

    while (!done) {
      const { value, done: chunkDone } = await reader.read();
      if (chunkDone) {
        done = true;
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      result += chunk;
      assistantMessage.textContent = result;
      scrollToBottom();
    }

    assistantMessage.innerHTML = escapeHtml(result.trim());
  } catch (error) {
    appendMessage("assistant", "Unable to send message. Check your connection.");
  } finally {
    isSending = false;
  }
}

function loadChat(chatId) {
  fetch(`/load_chat/${chatId}`)
    .then((res) => res.json())
    .then((data) => {
      chatWindow.innerHTML = "";
      data.messages.forEach((message) => {
        appendMessage(message.role, message.content);
      });
    });
}

document.addEventListener("DOMContentLoaded", () => {
  autoResizeTextarea();

  chatList?.querySelectorAll(".history-item").forEach((item) => {
    item.addEventListener("click", () => {
      const chatId = item.dataset.chatId;
      if (chatId) loadChat(chatId);
    });
  });

  newChatButton?.addEventListener("click", async () => {
    const response = await fetch("/new_chat", { method: "POST" });
    if (!response.ok) return;
    const data = await response.json();
    if (data.chat_id) window.location.reload();
  });

  messageInput?.addEventListener("input", autoResizeTextarea);
  messageInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const text = messageInput.value.trim();
      if (text) sendMessage(text);
    }
  });

  messageForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = messageInput.value.trim();
    if (text) sendMessage(text);
  });
});