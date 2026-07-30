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

// ─── Auto-resize Textarea ─────────────────────────────────────────────────

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 180) + "px";
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

// ─── New Chat ─────────────────────────────────────────────────────────────

newChatButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/new_chat", { method: "POST" });
    const data = await response.json();

    if (data.success || data.chat_id) {
      chatBox.innerHTML = `
        <div class="welcome">
          <h2>Welcome to Shani GPT</h2>
          <p>Start a new conversation by asking a question.</p>
        </div>
      `;
      input.value = "";
      input.style.height = "52px";
      input.focus();
      lastUserMessage = "";
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

// ─── Load Chat History Items ──────────────────────────────────────────────

function loadChat(chatId) {
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

chatList?.querySelectorAll(".history-item").forEach((item) => {
  item.addEventListener("click", function () {
    const chatId = this.dataset.chatId;
    if (chatId) {
      loadChat(chatId);
      document.querySelectorAll(".history-item").forEach((el) => el.classList.remove("active"));
      this.classList.add("active");
    }
    toggleSidebar(false);
  });

  item.addEventListener("keydown", (event) => {
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