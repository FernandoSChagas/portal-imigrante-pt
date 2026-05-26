// =====================================================================
// SESSÃO DE UTILIZADOR (Memória)
// =====================================================================
if (!localStorage.getItem("chat_session_id")) {
    const randomId = "sess_" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("chat_session_id", randomId);
}
const session_id = localStorage.getItem("chat_session_id");

const API_URL = "https://portal-imigrante-pt.onrender.com/api/chat";

// Inicialização automática do ecrã
document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chatBox");
    if (chatBox) {
        renderizarHistoricoLocal();
        
        // Ativa o clique do Enter no campo de texto de forma segura
        const userInput = document.getElementById("userInput");
        if (userInput) {
            userInput.addEventListener("keypress", (event) => {
                if (event.key === "Enter") {
                    enviarMensagem();
                }
            });
        }
    }
});

function renderizarHistoricoLocal() {
    const chatBox = document.getElementById("chatBox");
    if (!chatBox) return;

    const historico = JSON.parse(localStorage.getItem("chat_history")) || [];
    chatBox.innerHTML = "";
    
    if (historico.length === 0) {
        appendMessage("bot", "Olá! Sou o Imigrante AI. Como posso ajudar com a tua jornada, voos ou burocracia hoje?");
        return;
    }
    
    historico.forEach(msg => appendMessage(msg.sender, msg.text));
}

function appendMessage(sender, text) {
    const chatBox = document.getElementById("chatBox");
    if (!chatBox) return;
    
    const div = document.createElement("div");
    div.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function enviarMensagem() {
    const input = document.getElementById("userInput");
    if (!input || !input.value.trim()) return;
    
    const texto = input.value.trim();
    appendMessage("user", texto);
    input.value = "";
    
    salvarNoHistoricoLocal("user", texto);
    appendMessage("bot", "A consultar o servidor...");
    
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: texto, session_id: session_id })
        });
        const data = await response.json();
        
        const chatBox = document.getElementById("chatBox");
        if (chatBox && chatBox.lastChild) {
            chatBox.removeChild(chatBox.lastChild);
        }
        
        appendMessage("bot", data.response);
        salvarNoHistoricoLocal("bot", data.response);
    } catch (error) {
        const chatBox = document.getElementById("chatBox");
        if (chatBox && chatBox.lastChild) {
            chatBox.removeChild(chatBox.lastChild);
        }
        appendMessage("bot", "[Erro de conexão]: Servidor em standby. Tenta novamente em alguns instantes.");
    }
}

function salvarNoHistoricoLocal(sender, text) {
    let historico = JSON.parse(localStorage.getItem("chat_history")) || [];
    historico.push({ sender, text });
    if (historico.length > 20) historico.shift();
    localStorage.setItem("chat_history", JSON.stringify(historico));
}
