/* ===========================
   SHANI GPT - MAIN SCRIPT
   Professional AI Chat Interface
   =========================== */

// ─── DOM References ───────────────────────────────────────────────────────

const form = document.getElementById("message-form");
const input = document.getElementById("message-input");
const chatBox = document.getElementById("chat-window");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat-btn");
const menuToggle = document.getElementById("menu-toggle");
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebar-overlay");
const chatList = document.getElementById("chat-list");

let isSending = false;
let lastUserMessage = "";

// ─── Configure Marked.js ──────────────────────────────────────────────────

if (typeof marked !== 'undefined') {
  marked.setOptions({
    breaks: true,
    gfm: true,
    highlight: function (code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value;
        } catch (e) {
          // fall through
        }
      }
      return code;
    }
  });
}

// ─── Utility Functions ────────────────────────────────────────────────────

function scrollToBottom() {
  requestAnimationFrame(() => {
    chatBox.scrollTo({
      top: chatBox.scrollHeight,
      behavior: "smooth"
    });
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ─── Copy Response Button ─────────────────────────────────────────────────

function addResponseCopyButton(container) {
  if (container.querySelector(".copy-response-btn")) return;

  const btn = document.createElement("button");
  btn.className = "copy-response-btn";
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy`;

  btn.addEventListener("click", async () => {
    const markdownBody = container.querySelector(".markdown-body");
    const textToCopy = markdownBody ? markdownBody.innerText : container.innerText;

    try {
      await navigator.clipboard.writeText(textToCopy);
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied ✓`;
      btn.classList.add("copied");
      setTimeout(() => {
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy`;
        btn.classList.remove("copied");
      }, 2000);
    } catch (err) {
      const textarea = document.createElement("textarea");
      textarea.value = textToCopy;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      btn.innerHTML = `Copied ✓`;
      btn.classList.add("copied");
      setTimeout(() => {
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy`;
        btn.classList.remove("copied");
      }, 2000);
    }
  });

  container.appendChild(btn);
}

// ─── Code Block Copy Buttons ──────────────────────────────────────────────

function addCodeCopyButtons() {
  const blocks = document.querySelectorAll(".markdown-body pre");

  blocks.forEach((block) => {
    if (block.querySelector(".copy-code-btn")) return;

    const button = document.createElement("button");
    button.className = "copy-code-btn";
    button.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy code`;

    button.addEventListener("click", async () => {
      const code = block.querySelector("code");
      const textToCopy = code ? code.innerText : block.innerText;

      try {
        await navigator.clipboard.writeText(textToCopy);
        button.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        button.classList.add("copied");
        setTimeout(() => {
          button.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy code`;
          button.classList.remove("copied");
        }, 2000);
      } catch (err) {
        const textarea = document.createElement("textarea");
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        button.textContent = "Copied!";
        button.classList.add("copied");
        setTimeout(() => {
          button.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy code`;
          button.classList.remove("copied");
        }, 2000);
      }
    });

    block.appendChild(button);
  });
}

// ─── Render Markdown Safely ───────────────────────────────────────────────

function renderMarkdown(text) {
  if (typeof marked !== 'undefined') {
    return marked.parse(text);
  }
  return escapeHtml(text).replace(/\n/g, '<br>');
}

// ─── Regenerate Response ──────────────────────────────────────────────────

function addRegenerateButton(aiMsgDiv, userMessageText) {
  const actionsRow = aiMsgDiv.querySelector(".ai-actions");
  if (!actionsRow || actionsRow.querySelector(".regenerate-btn")) return;

  const btn = document.createElement("button");
  btn.className = "regenerate-btn";
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg> Regenerate`;

  btn.addEventListener("click", async () => {
    if (btn.classList.contains("regenerating")) return;
    btn.classList.add("regenerating");
    btn.innerHTML = `<div class="regenerating-spinner"></div> Regenerating...`;

    // Find the AI content and markdown body within this message
    const aiContent = aiMsgDiv.querySelector(".ai-content");
    const markdownBody = aiMsgDiv.querySelector(".markdown-body");

    // Show loading state in the message
    if (markdownBody) {
      markdownBody.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
    }

    try {
      const response = await fetch("/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessageText })
      });

      if (!response.ok) throw new Error("Server error: " + response.status);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullReply = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        fullReply += chunk;
        if (markdownBody) {
          markdownBody.innerHTML = renderMarkdown(fullReply);
        }
        scrollToBottom();
      }

      // Re-highlight code blocks
      if (markdownBody && typeof hljs !== 'undefined') {
        markdownBody.querySelectorAll('pre code').forEach((block) => {
          hljs.highlightElement(block);
        });
      }
      addCodeCopyButtons();

    } catch (error) {
      if (markdownBody) {
        markdownBody.innerHTML = `<div style="color: #fca5a5;">❌ Error regenerating response. Please try again.</div>`;
      }
    }

    btn.classList.remove("regenerating");
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg> Regenerate`;
  });

  actionsRow.appendChild(btn);
}

// ─── Like / Dislike Feedback Buttons ──────────────────────────────────────

function addFeedbackButtons(aiContent) {
  if (aiContent.querySelector(".feedback-btn-group")) return;

  const group = document.createElement("div");
  group.className = "feedback-btn-group";

  // Like button
  const likeBtn = document.createElement("button");
  likeBtn.className = "feedback-btn like-btn";
  likeBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>`;
  likeBtn.title = "Like";

  // Dislike button
  const dislikeBtn = document.createElement("button");
  dislikeBtn.className = "feedback-btn dislike-btn";
  dislikeBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path></svg>`;
  dislikeBtn.title = "Dislike";

  // Helper to send feedback to the backend
  function sendFeedback(feedbackType) {
    // Find the parent AI message wrapper to get the chat_sa_id
    const aiMsgWrapper = aiContent.closest(".ai-message-wrapper");
    const chatSaId = aiMsgWrapper ? aiMsgWrapper.dataset.chatSaId : null;

    if (!chatSaId) {
      console.warn("No chat_sa_id found for feedback. Chat may not have been saved yet.");
      return;
    }

    fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: parseInt(chatSaId),
        feedback_type: feedbackType
      })
    }).then(res => res.json()).then(data => {
      if (!data.success) {
        console.warn("Feedback API returned error:", data.error);
      }
    }).catch(err => console.error("Failed to submit feedback:", err));
  }

  likeBtn.addEventListener("click", () => {
    const wasLiked = likeBtn.classList.contains("active");
    // Toggle: if already liked, un-like; otherwise like and remove dislike
    likeBtn.classList.toggle("active", !wasLiked);
    dislikeBtn.classList.remove("active");

    // Send feedback to backend
    if (!wasLiked) {
      sendFeedback("like");
    } else {
      sendFeedback("none");
    }
  });

  dislikeBtn.addEventListener("click", () => {
    const wasDisliked = dislikeBtn.classList.contains("active");
    // Toggle: if already disliked, un-dislike; otherwise dislike and remove like
    dislikeBtn.classList.toggle("active", !wasDisliked);
    likeBtn.classList.remove("active");

    // Send feedback to backend
    if (!wasDisliked) {
      sendFeedback("dislike");
    } else {
      sendFeedback("none");
    }
  });

  group.appendChild(likeBtn);
  group.appendChild(dislikeBtn);
  aiContent.appendChild(group);
}

// ─── Add Action Buttons Row (Copy, Regenerate, Feedback) ──────────────────

function addActionButtons(aiMsgDiv, userMessageText) {
  const aiContent = aiMsgDiv.querySelector(".ai-content");
  if (!aiContent) return;

  // Create actions row if it doesn't exist
  let actionsRow = aiContent.querySelector(".ai-actions");
  if (!actionsRow) {
    actionsRow = document.createElement("div");
    actionsRow.className = "ai-actions";
    aiContent.appendChild(actionsRow);
  }

  // Add copy button
  addResponseCopyButton(aiContent);

  // Add regenerate button
  addRegenerateButton(aiMsgDiv, userMessageText);

  // Add feedback buttons
  addFeedbackButtons(aiContent);
}

// ─── Auto-resize Textarea + Send Button State ─────────────────────────────

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 180) + "px";
  // Enable/disable send button based on input content
  const hasText = input.value.trim().length > 0;
  sendButton.disabled = hasText ? false : true;
});

// ─── Enter to Send, Shift+Enter for New Line ──────────────────────────────

input.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.dispatchEvent(new Event("submit"));
  }
});

// ─── Send Message ─────────────────────────────────────────────────────────

form.addEventListener("submit", async function (e) {
  e.preventDefault();

  const message = input.value.trim();
  if (message === "" || isSending) return;
  isSending = true;

  // Store the last user message for regenerate
  lastUserMessage = message;

  // Disable input while waiting
  input.disabled = true;
  sendButton.disabled = true;

  // Hide welcome message
  const welcome = document.querySelector(".welcome");
  if (welcome) {
    welcome.remove();
  }

  // Add user message
  const userMsgDiv = document.createElement("div");
  userMsgDiv.className = "message user-message-wrapper";
  userMsgDiv.innerHTML = `
    <div class="message-content user-content">${escapeHtml(message)}</div>
  `;
  chatBox.appendChild(userMsgDiv);
  scrollToBottom();

  // Clear input
  input.value = "";
  input.style.height = "52px";

  // Add typing indicator
  const typingDiv = document.createElement("div");
  typingDiv.className = "message ai-message-wrapper";
  typingDiv.id = "thinking";
  typingDiv.innerHTML = `
    <div class="message-avatar">S</div>
    <div class="message-content ai-content">
      <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;
  chatBox.appendChild(typingDiv);
  scrollToBottom();

  try {
    const response = await fetch("/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message: message })
    });

    if (!response.ok) {
      throw new Error("Server error: " + response.status);
    }

    // Remove typing indicator
    const thinkingEl = document.getElementById("thinking");
    if (thinkingEl) thinkingEl.remove();

    // Create AI message container
    const aiMsgDiv = document.createElement("div");
    aiMsgDiv.className = "message ai-message-wrapper";
    aiMsgDiv.innerHTML = `
      <div class="message-avatar">S</div>
      <div class="message-content ai-content">
        <div class="markdown-body" id="streaming-message"></div>
      </div>
    `;
    chatBox.appendChild(aiMsgDiv);
    scrollToBottom();

    const messageBox = document.getElementById("streaming-message");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullReply = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      fullReply += chunk;
      messageBox.innerHTML = renderMarkdown(fullReply);
      scrollToBottom();
    }

    // Add action buttons (copy, regenerate, feedback)
    addActionButtons(aiMsgDiv, message);

    // Add code copy buttons
    addCodeCopyButtons();

    // Highlight code blocks
    if (typeof hljs !== 'undefined') {
      messageBox.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
      });
    }

    // Save conversation to SQLAlchemy database for admin dashboard
    // This stores the user message + AI response pair in the ChatSA model
    fetch("/save_chat_sa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_message: message,
        ai_response: fullReply
      })
    }).then(res => res.json()).then(data => {
      if (data.success && data.chat_id) {
        // Store the chat_sa_id on the AI message div for feedback
        aiMsgDiv.dataset.chatSaId = data.chat_id;
      }
    }).catch(err => console.error("Failed to save chat for admin:", err));

  } catch (error) {
    const thinkingEl = document.getElementById("thinking");
    if (thinkingEl) thinkingEl.remove();

    const errorDiv = document.createElement("div");
    errorDiv.className = "message ai-message-wrapper";
    errorDiv.innerHTML = `
      <div class="message-avatar">S</div>
      <div class="message-content ai-content">
        <div style="color: #fca5a5;">❌ Error connecting to Shani GPT. Please try again.</div>
      </div>
    `;
    chatBox.appendChild(errorDiv);
    scrollToBottom();
  }

  // Re-enable input
  input.disabled = false;
  sendButton.disabled = false;
  isSending = false;
  input.focus();
});

// ─── Suggestion Cards ──────────────────────────────────────────────────────

function attachSuggestionCardListeners() {
  document.querySelectorAll(".suggestion-card").forEach((card) => {
    card.addEventListener("click", function () {
      const prompt = this.getAttribute("data-prompt");
      if (prompt) {
        input.value = prompt;
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 180) + "px";
        sendButton.disabled = false;
        input.focus();
      }
    });
  });
}

// ─── New Chat ─────────────────────────────────────────────────────────────

newChatButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/new_chat", { method: "POST" });
    const data = await response.json();

    if (data.success || data.chat_id) {
      chatBox.innerHTML = `
        <div class="welcome">
          <h2>What can I help with today?</h2>
          <div class="suggestion-cards">
            <button class="suggestion-card" data-prompt="Summarize a document or article for me">
              <span class="suggestion-icon">📄</span>
              <span class="suggestion-text">Summarize a document</span>
            </button>
            <button class="suggestion-card" data-prompt="Write a Python function that calculates the Fibonacci sequence">
              <span class="suggestion-icon">💻</span>
              <span class="suggestion-text">Write code</span>
            </button>
            <button class="suggestion-card" data-prompt="Help me brainstorm creative ideas for">
              <span class="suggestion-icon">💡</span>
              <span class="suggestion-text">Brainstorm ideas</span>
            </button>
            <button class="suggestion-card" data-prompt="Explain the concept of quantum computing in simple terms">
              <span class="suggestion-icon">🔬</span>
              <span class="suggestion-text">Explain a concept</span>
            </button>
            <button class="suggestion-card" data-prompt="Write a professional email about">
              <span class="suggestion-icon">✉️</span>
              <span class="suggestion-text">Draft an email</span>
            </button>
            <button class="suggestion-card" data-prompt="Create a study plan for learning">
              <span class="suggestion-icon">📚</span>
              <span class="suggestion-text">Create a study plan</span>
            </button>
          </div>
        </div>
      `;
      input.value = "";
      input.style.height = "52px";
      input.focus();
      lastUserMessage = "";
      attachSuggestionCardListeners();
    }
  } catch (error) {
    console.error("Failed to create new chat:", error);
  }
});

// ─── Sidebar Toggle ───────────────────────────────────────────────────────

function toggleSidebar(force) {
  if (!sidebar) return;
  const shouldOpen = typeof force === "boolean" ? force : !sidebar.classList.contains("open");
  sidebar.classList.toggle("open", shouldOpen);
  sidebarOverlay?.classList.toggle("active", shouldOpen);
  menuToggle?.setAttribute("aria-label", shouldOpen ? "Close sidebar" : "Open sidebar");
  document.body.classList.toggle("drawer-open", shouldOpen);
}

menuToggle.addEventListener("click", () => toggleSidebar());

sidebarOverlay.addEventListener("click", () => toggleSidebar(false));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") toggleSidebar(false);
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 1024) toggleSidebar(false);
});

// ─── Date Grouping ─────────────────────────────────────────────────────────

function getDateLabel(dateStr) {
  if (!dateStr) return "Older";
  const date = new Date(dateStr);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  if (date >= today) return "Today";
  if (date >= yesterday) return "Yesterday";
  if (date >= weekAgo) return "Previous 7 Days";
  return "Older";
}

function groupChatsByDate(chats) {
  const groups = {};
  chats.forEach((chat) => {
    const label = getDateLabel(chat.created_at);
    if (!groups[label]) groups[label] = [];
    groups[label].push(chat);
  });
  return groups;
}

function renderChatList(chats) {
  const chatListEl = document.getElementById("chat-list");
  if (!chatListEl) return;

  const order = ["Today", "Yesterday", "Previous 7 Days", "Older"];
  const grouped = groupChatsByDate(chats);
  const currentChatId = document.querySelector(".history-item.active")?.dataset.chatId;

  let html = "";
  order.forEach((label) => {
    if (grouped[label] && grouped[label].length > 0) {
      html += `<div class="date-group"><div class="date-label">${label}</div>`;
      grouped[label].forEach((chat) => {
        const activeClass = chat.id.toString() === currentChatId ? "active" : "";
        html += `
          <div class="history-item ${activeClass}" data-chat-id="${chat.id}" data-created-at="${chat.created_at || ""}" role="button" tabindex="0" aria-pressed="false">
            <span class="history-item-title">${escapeHtml(chat.title)}</span>
            <div class="history-item-actions">
              <button class="history-action-btn rename-btn" data-chat-id="${chat.id}" title="Rename">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
              </button>
              <button class="history-action-btn delete-btn" data-chat-id="${chat.id}" title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </div>
          </div>
        `;
      });
      html += "</div>";
    }
  });

  chatListEl.innerHTML = html;
  attachChatItemListeners();
}

// ─── Search Chats ─────────────────────────────────────────────────────────

function initChatSearch() {
  const searchInput = document.getElementById("history-search");
  if (!searchInput) return;

  let debounceTimer;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const query = searchInput.value.trim();
      if (!query) {
        renderChatList(window.__allChats || []);
        return;
      }
      fetch(`/search_chats?q=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((results) => {
          renderChatList(results);
        })
        .catch((err) => console.error("Search failed:", err));
    }, 250);
  });
}

// ─── Rename Chat (Inline Edit) ─────────────────────────────────────────────

function handleRenameClick(e, renameBtn) {
  e.stopPropagation();
  e.preventDefault();

  const chatId = renameBtn.dataset.chatId;
  const historyItem = renameBtn.closest(".history-item");
  const titleEl = historyItem?.querySelector(".history-item-title");
  if (!chatId || !titleEl) return;

  const currentTitle = titleEl.textContent.trim();

  // Replace title text with an inline input
  const input = document.createElement("input");
  input.type = "text";
  input.className = "rename-input";
  input.value = currentTitle;
  input.setAttribute("maxlength", "60");

  // Replace the title span with the input
  titleEl.replaceWith(input);
  input.focus();
  input.select();

  let saved = false;

  function saveRename() {
    if (saved) return;
    saved = true;
    const trimmed = input.value.trim();
    if (!trimmed || trimmed === currentTitle) {
      // No change — restore original title
      const span = document.createElement("span");
      span.className = "history-item-title";
      span.textContent = currentTitle;
      input.replaceWith(span);
      return;
    }

    fetch("/rename_chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: parseInt(chatId), title: trimmed })
    })
      .then((res) => res.json())
      .then((data) => {
        const span = document.createElement("span");
        span.className = "history-item-title";
        span.textContent = data.success ? trimmed : currentTitle;
        input.replaceWith(span);
        // Update header if this is the active chat
        if (data.success) {
          const activeItem = document.querySelector(".history-item.active");
          if (activeItem && activeItem.dataset.chatId === chatId) {
            document.querySelector("header h1").textContent = trimmed;
          }
        }
      })
      .catch((err) => {
        console.error("Rename failed:", err);
        const span = document.createElement("span");
        span.className = "history-item-title";
        span.textContent = currentTitle;
        input.replaceWith(span);
      });
  }

  function cancelRename() {
    if (saved) return;
    saved = true;
    const span = document.createElement("span");
    span.className = "history-item-title";
    span.textContent = currentTitle;
    input.replaceWith(span);
  }

  // Save on Enter or blur
  input.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      ev.preventDefault();
      saveRename();
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      cancelRename();
    }
  });

  input.addEventListener("blur", saveRename);
}

// ─── Delete Chat ──────────────────────────────────────────────────────────

function handleDeleteClick(e, deleteBtn) {
  e.stopPropagation();
  e.preventDefault();

  const chatId = deleteBtn.dataset.chatId;
  const historyItem = deleteBtn.closest(".history-item");
  if (!chatId || !historyItem) return;

  if (!confirm("Delete this chat? This cannot be undone.")) return;

  fetch(`/delete_chat/${chatId}`, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success || data.chat_id) {
        historyItem.remove();
        // If deleted chat was active, load the new active chat or show welcome
        const activeItem = document.querySelector(".history-item.active");
        if (!activeItem) {
          if (data.chat_id) {
            loadChat(data.chat_id);
          } else {
            chatBox.innerHTML = `
              <div class="welcome">
                <h2>What can I help with today?</h2>
                <div class="suggestion-cards">
                  <button class="suggestion-card" data-prompt="Summarize a document or article for me">
                    <span class="suggestion-icon">📄</span>
                    <span class="suggestion-text">Summarize a document</span>
                  </button>
                  <button class="suggestion-card" data-prompt="Write a Python function that calculates the Fibonacci sequence">
                    <span class="suggestion-icon">💻</span>
                    <span class="suggestion-text">Write code</span>
                  </button>
                  <button class="suggestion-card" data-prompt="Help me brainstorm creative ideas for">
                    <span class="suggestion-icon">💡</span>
                    <span class="suggestion-text">Brainstorm ideas</span>
                  </button>
                  <button class="suggestion-card" data-prompt="Explain the concept of quantum computing in simple terms">
                    <span class="suggestion-icon">🔬</span>
                    <span class="suggestion-text">Explain a concept</span>
                  </button>
                  <button class="suggestion-card" data-prompt="Write a professional email about">
                    <span class="suggestion-icon">✉️</span>
                    <span class="suggestion-text">Draft an email</span>
                  </button>
                  <button class="suggestion-card" data-prompt="Create a study plan for learning">
                    <span class="suggestion-icon">📚</span>
                    <span class="suggestion-text">Create a study plan</span>
                  </button>
                </div>
              </div>
            `;
            attachSuggestionCardListeners();
            document.querySelector("header h1").textContent = "Shani GPT";
          }
        }
      }
    })
    .catch((err) => console.error("Delete failed:", err));
}

// ─── Refresh Chat List ────────────────────────────────────────────────────

function refreshChatList() {
  // Reload the page to refresh the chat list from server-side data
  // This is simpler and avoids needing a dedicated API endpoint
  window.location.reload();
}

// ─── Sidebar Collapse ─────────────────────────────────────────────────────

function initSidebarCollapse() {
  const collapseBtn = document.getElementById("sidebar-collapse-btn");
  const sidebar = document.getElementById("sidebar");
  if (!collapseBtn || !sidebar) return;

  collapseBtn.addEventListener("click", () => {
    const isCollapsed = sidebar.classList.toggle("collapsed");
    collapseBtn.classList.toggle("collapsed", isCollapsed);
    collapseBtn.title = isCollapsed ? "Expand sidebar" : "Collapse sidebar";
  });
}

// ─── Load Chat History Items ──────────────────────────────────────────────

function attachChatItemListeners() {
  document.querySelectorAll(".history-item").forEach((item) => {
    // Click handler for opening a chat
    item.addEventListener("click", function (e) {
      // Don't trigger if clicking action buttons
      if (e.target.closest(".history-action-btn")) return;
      const chatId = this.dataset.chatId;
      if (chatId) {
        loadChat(chatId);
        document.querySelectorAll(".history-item").forEach((el) => el.classList.remove("active"));
        this.classList.add("active");
      }
      toggleSidebar(false);
    });

    // Keyboard handler for accessibility
    item.addEventListener("keydown", (event) => {
      // Don't trigger shortcuts when typing in an input or textarea
      if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA") return;
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        const chatId = item.dataset.chatId;
        if (chatId) {
          loadChat(chatId);
          document.querySelectorAll(".history-item").forEach((el) => el.classList.remove("active"));
          item.classList.add("active");
        }
        toggleSidebar(false);
      }
    });
  });

  // Attach rename button handlers
  document.querySelectorAll(".rename-btn").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      handleRenameClick(e, this);
    });
  });

  // Attach delete button handlers
  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      handleDeleteClick(e, this);
    });
  });
}

function showChatSkeleton() {
  chatBox.innerHTML = `
    <div class="skeleton-message">
      <div class="skeleton-avatar"></div>
      <div class="skeleton-bubble">
        <div class="skeleton-line" style="width: 80%;"></div>
        <div class="skeleton-line" style="width: 60%;"></div>
      </div>
    </div>
    <div class="skeleton-message" style="justify-content: flex-end; padding-left: 60px;">
      <div class="skeleton-bubble" style="max-width: 50%; background: #1e293b;">
        <div class="skeleton-line" style="width: 70%;"></div>
      </div>
    </div>
    <div class="skeleton-message">
      <div class="skeleton-avatar"></div>
      <div class="skeleton-bubble">
        <div class="skeleton-line" style="width: 90%;"></div>
        <div class="skeleton-line" style="width: 75%;"></div>
        <div class="skeleton-line" style="width: 50%;"></div>
      </div>
    </div>
  `;
}

function loadChat(chatId) {
  showChatSkeleton();
  fetch(`/load_chat/${chatId}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.messages) {
        chatBox.innerHTML = "";
        data.messages.forEach((msg) => {
          if (msg.role === "user") {
            const div = document.createElement("div");
            div.className = "message user-message-wrapper";
            div.innerHTML = `<div class="message-content user-content">${escapeHtml(msg.content)}</div>`;
            chatBox.appendChild(div);
          } else {
            const div = document.createElement("div");
            div.className = "message ai-message-wrapper";
            div.innerHTML = `
              <div class="message-avatar">S</div>
              <div class="message-content ai-content">
                <div class="markdown-body">${renderMarkdown(msg.content)}</div>
              </div>
            `;
            chatBox.appendChild(div);
            // Add copy button only (no regenerate/feedback for history)
            const aiContent = div.querySelector(".ai-content");
            addResponseCopyButton(aiContent);
          }
        });

        if (data.title) {
          document.querySelector("header h1").textContent = data.title;
        }

        scrollToBottom();
        addCodeCopyButtons();
      }
    })
    .catch((error) => console.error("Failed to load chat:", error));
}

// ─── Initialize - DOM Ready ──────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  if (input) {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 180) + "px";
  }

  input?.focus();

  // Render server-side markdown content from data-raw-content attributes
  document.querySelectorAll(".markdown-body[data-raw-content]").forEach((el) => {
    const rawContent = el.getAttribute("data-raw-content");
    if (rawContent) {
      el.innerHTML = renderMarkdown(rawContent);
      el.removeAttribute("data-raw-content");
    }
  });

  // Attach suggestion card click handlers
  attachSuggestionCardListeners();

  // Attach click handlers to initial server-rendered chat items
  // (includes rename/delete button handlers)
  attachChatItemListeners();

  // Initialize sidebar features
  initChatSearch();
  initSidebarCollapse();

  // Cache initial chat list for search restore
  window.__allChats = Array.from(document.querySelectorAll(".history-item")).map((item) => ({
    id: parseInt(item.dataset.chatId),
    title: item.querySelector(".history-item-title")?.textContent || "",
    created_at: item.dataset.createdAt || ""
  }));

  // Add copy buttons to any existing AI messages from server-side rendering
  document.querySelectorAll(".ai-message-wrapper .ai-content").forEach((container) => {
    addResponseCopyButton(container);
  });
  addCodeCopyButtons();

  if (typeof hljs !== 'undefined') {
    document.querySelectorAll('.markdown-body pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }
});