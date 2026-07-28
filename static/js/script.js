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
  // Don't add twice
  if (container.querySelector(".copy-response-btn")) return;

  const btn = document.createElement("button");
  btn.className = "copy-response-btn";
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy`;

  btn.addEventListener("click", async () => {
    // Get the text content of the markdown body (without HTML tags)
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
      // Fallback for older browsers
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
    // Don't add twice
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
        // Fallback
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
  // Fallback: escape HTML and preserve line breaks
  return escapeHtml(text).replace(/\n/g, '<br>');
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

    // Add copy button to the response
    const aiContent = aiMsgDiv.querySelector(".ai-content");
    addResponseCopyButton(aiContent);

    // Add code copy buttons
    addCodeCopyButtons();

    // Highlight code blocks
    if (typeof hljs !== 'undefined') {
      messageBox.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
      });
    }

  } catch (error) {
    // Remove typing indicator if still present
    const thinkingEl = document.getElementById("thinking");
    if (thinkingEl) thinkingEl.remove();

    // Show error message
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

// Close sidebar on Escape key
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") toggleSidebar(false);
});

// Close sidebar on window resize above tablet
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
            // Add copy button
            const aiContent = div.querySelector(".ai-content");
            addResponseCopyButton(aiContent);
          }
        });

        // Update title
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
      // Update active state
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
        // Update active state
        document.querySelectorAll(".history-item").forEach((el) => el.classList.remove("active"));
        item.classList.add("active");
      }
      toggleSidebar(false);
    }
  });
});

// ─── Initialize - DOM Ready ──────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Auto-resize textarea initially
  if (input) {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 180) + "px";
  }

  // Focus input
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

  // Highlight any code blocks in server-rendered content
  if (typeof hljs !== 'undefined') {
    document.querySelectorAll('.markdown-body pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }
});
