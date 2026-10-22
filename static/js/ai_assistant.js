document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector(".chat-form");
    const input = document.querySelector("input[name='message']");
    const chatArea = document.querySelector(".chat-area");

    const quickButtons = document.querySelectorAll(".quick-questions button");


    // =====================================================
    // SEND MESSAGE TO AI
    // =====================================================

    function sendMessage(message) {

        message = message.trim();

        if (message === "") {
            return;
        }


        // =================================================
        // SHOW CUSTOMER MESSAGE
        // =================================================

        const customerMessage = document.createElement("div");

        customerMessage.className = "message user-message";

        customerMessage.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;

        chatArea.appendChild(customerMessage);


        // =================================================
        // SEND TO DJANGO
        // =================================================

        fetch("/ai-assistant/chat/", {

            method: "POST",

            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": document.querySelector(
                    "[name=csrfmiddlewaretoken]"
                ).value
            },

            body: new URLSearchParams({
                message: message
            })

        })

        .then(response => response.json())

        .then(data => {

            // =============================================
            // SHOW AI RESPONSE
            // =============================================

            const aiMessage = document.createElement("div");

            aiMessage.className = "message ai-message";

            aiMessage.innerHTML = `
                <div class="message-icon">
                    🤖
                </div>

                <div class="message-content">
                    <p>${data.response}</p>
                </div>
            `;

            chatArea.appendChild(aiMessage);

            // Scroll to latest message
            chatArea.scrollTop = chatArea.scrollHeight;

        })

        .catch(error => {

            console.error("AI Error:", error);

            const errorMessage = document.createElement("div");

            errorMessage.className = "message ai-message";

            errorMessage.innerHTML = `
                <div class="message-icon">
                    🤖
                </div>

                <div class="message-content">
                    <p>
                        Sorry, something went wrong.
                        Please try again.
                    </p>
                </div>
            `;

            chatArea.appendChild(errorMessage);

        });

    }


    // =====================================================
    // NORMAL MESSAGE FORM
    // =====================================================

    form.addEventListener("submit", function (event) {

        event.preventDefault();

        const message = input.value.trim();

        if (message === "") {
            return;
        }

        input.value = "";

        sendMessage(message);

    });


    // =====================================================
    // QUICK QUESTION BUTTONS
    // =====================================================

    quickButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const question = button.textContent.trim();

            sendMessage(question);

        });

    });

});