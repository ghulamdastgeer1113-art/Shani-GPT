function scrollToBottom() {

    const chatBox = document.getElementById("chat-box");

    chatBox.scrollTo({

        top: chatBox.scrollHeight,

        behavior: "smooth"

    });

}