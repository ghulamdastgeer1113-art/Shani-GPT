function addCopyButtons() {

    const blocks = document.querySelectorAll(".markdown-body pre");

    blocks.forEach((block) => {

        // Don't add twice
        if (block.querySelector(".copy-btn")) return;

        const button = document.createElement("button");

        button.className = "copy-btn";

        button.textContent = "📋 Copy";

        button.onclick = () => {

            navigator.clipboard.writeText(
                block.querySelector("code").innerText
            );

            button.textContent = "✅ Copied!";

            setTimeout(() => {

                button.textContent = "📋 Copy";

            }, 2000);

        };

        block.style.position = "relative";

        block.appendChild(button);

    });

}
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const chatBox = document.getElementById("chat-box");
const sendButton = form.querySelector("button");
const newChatButton = document.getElementById("new-chat");

// Scroll to bottom
function scrollToBottom() {
    chatBox.scrollTo({
        top: chatBox.scrollHeight,
        behavior: "smooth"
    });
}

// Auto resize textarea
input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = input.scrollHeight + "px";
});

// Enter = Send
// Shift + Enter = New Line
input.addEventListener("keydown", function (e) {

    if (e.key === "Enter" && !e.shiftKey) {

        e.preventDefault();

        form.dispatchEvent(new Event("submit"));

    }

});

form.addEventListener("submit", async function (e) {

    e.preventDefault();

    const message = input.value.trim();

    if (message === "") return;

    // Disable input while waiting
    input.disabled = true;
    sendButton.disabled = true;

    // Hide welcome message
    const welcome = document.querySelector(".welcome");
    if (welcome) {
        welcome.remove();
    }

    // User message
    chatBox.innerHTML += `
        <div class="user-container">
            <div class="user-message">
                ${message}
            </div>
        </div>
    `;

    scrollToBottom();

    input.value = "";
    input.style.height = "52px";

    // Thinking message
    chatBox.innerHTML += `
<div class="ai-container" id="thinking">
    <div class="ai-message">
        <div class="typing">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
</div>
`

    

    scrollToBottom();

   try {

    const response = await fetch("/stream", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            message: message
        })

    });

    // Remove thinking animation
    document.getElementById("thinking").remove();

    // Create an empty AI message
    chatBox.innerHTML += `
    <div class="ai-container">
        <div class="ai-message">
            <div class="ai-header">
                🤖 <strong>Shani GPT</strong>
            </div>

            <div class="markdown-body" id="streaming-message"></div>
        </div>
    </div>
    `;

    const messageBox = document.getElementById("streaming-message");

    const reader = response.body.getReader();

    const decoder = new TextDecoder();

    let fullReply = "";

    while (true) {

        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);

        fullReply += chunk;

        messageBox.innerHTML = marked.parse(fullReply);

        scrollToBottom();

    }

    addCopyButtons();

    hljs.highlightAll();

} catch (error) {

    document.getElementById("thinking")?.remove();

    chatBox.innerHTML += `
    <div class="ai-container">
        <div class="ai-message">
            ❌ Error connecting to Shani GPT.
        </div>
    </div>
    `;

}

        document.getElementById("thinking").remove();

        chatBox.innerHTML += `
            <div class="ai-container">
                <div class="ai-message">
                    ❌ Error connecting to Shani GPT.
                </div>
            </div>
        `;

    

    input.disabled = false;
    sendButton.disabled = false;

    input.focus();

    scrollToBottom();

});
newChatButton.addEventListener("click", async () => {

    const response = await fetch("/new_chat", {
        method: "POST"
    });

    const data = await response.json();

    if (data.success) {

        // Clear chat area
        chatBox.innerHTML = `
            <div class="welcome">
                👋 Hello! I'm <b>Shani GPT</b>.<br><br>
                Ask me anything!
            </div>
        `;

        input.value = "";
        input.focus();

    }

});