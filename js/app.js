// =====================================================================
// GESTÃO DE SESSÃO DO UTILIZADOR (Memória Humana)
// =====================================================================
if (!localStorage.getItem("chat_session_id")) {
    const randomId = "sess_" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("chat_session_id", randomId);
}
const session_id = localStorage.getItem("chat_session_id");

// URL oficial do teu back-end hospedado no Render
const API_URL = "https://portal-imigrante-pt.onrender.com/api/chat";

// Inicializa o chat assim que a página assistente.html estiver carregada
document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    if (chatBox) {
        renderizarHistoricoLocal();
    }
});

// =====================================================================
// LÓGICA DO FLUXO DE MENSAGENS
// =====================================================================
function renderizarHistoricoLocal() {
    const chatBox = document.getElementById("chat-box");
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
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;
    
    const div = document.createElement("div");
    // Garante compatibilidade com as classes CSS (user-message / bot-message / msg)
    div.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function enviarMensagem() {
    const input = document.getElementById("user-input");
    if (!input || !input.value.trim()) return;
    
    const texto = input.value.trim();
    appendMessage("user", texto);
    input.value = "";
    
    // Grava a pergunta no histórico local
    salvarNoHistoricoLocal("user", texto);
    
    // Feedback visual de carregamento
    appendMessage("bot", "A consultar o servidor...");
    
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: texto, session_id: session_id })
        });
        const data = await response.json();
        
        // Remove a mensagem temporária de "A consultar..."
        const chatBox = document.getElementById("chat-box");
        if (chatBox && chatBox.lastChild) {
            chatBox.removeChild(chatBox.lastChild);
        }
        
        appendMessage("bot", data.response);
        salvarNoHistoricoLocal("bot", data.response);
    } catch (error) {
        const chatBox = document.getElementById("chat-box");
        if (chatBox && chatBox.lastChild) {
            chatBox.removeChild(chatBox.lastChild);
        }
        appendMessage("bot", "[Erro de conexão]: Não consegui alcançar o servidor. Tenta novamente.");
    }
}

// Permite enviar a mensagem pressionando a tecla Enter
function verificarTecla(event) {
    if (event.key === "Enter") {
        enviarMensagem();
    }
}

function salvarNoHistoricoLocal(sender, text) {
    let historico = JSON.parse(localStorage.getItem("chat_history")) || [];
    historico.push({ sender, text });
    if (historico.length > 20) historico.shift(); // Evita sobrecarregar o navegador
    localStorage.setItem("chat_history", JSON.stringify(historico));
}
