document.addEventListener("DOMContentLoaded", () => {
    // ELEMENTOS DO CHAT
    const inputChat = document.querySelector(".chat-input-area input");
    const btnEnviar = document.querySelector(".btn-enviar");
    const chatWindow = document.querySelector(".chat-window");

    // ELEMENTOS DOS GUIAS DINÂMICOS
    const areaGuiaDinamico = document.getElementById("area-guia-dinamico");
    const corpoTextoGuia = document.getElementById("corpo-texto-guia");
    const btnFecharGuia = document.getElementById("btn-fechar-guia");

    // ELEMENTOS DA CALCULADORA
    const inputAlojamento = document.getElementById("calc-alojamento");
    const inputAlimentacao = document.getElementById("calc-alimentacao");
    const inputTransportes = document.getElementById("calc-transportes");
    const inputExtras = document.getElementById("calc-extras");
    const txtTotalCusto = document.getElementById("total-custo");

    // ELEMENTOS DO SISTEMA DE BUSCA DE PORTAIS
    const searchInput = document.getElementById("search-service-input");
    const categorySelect = document.getElementById("filter-category-select");
    const servicesGridContainer = document.getElementById("services-grid-container");

    // BASE DE DADOS CANAIS OFICIAIS
    const dadosServicos = [
        {
            nome: "PORTAL DAS FINANÇAS (AUTORIDADE TRIBUTÁRIA)",
            categoria: "saude-fiscal",
            categoriaTexto: "Finanças & Fiscalidade",
            endereco: "Serviços de Finanças Locais e Atendimento e-Balcão",
            url: "https://www.portaldasfinancas.gov.pt",
            icone: "⚖️"
        },
        {
            nome: "AIMA - AGÊNCIA PARA A INTEGRAÇÃO, MIGRAÇÕES E ASILO",
            categoria: "documentos",
            categoriaTexto: "Documentação & Vistos",
            endereco: "Lojas AIMA e Postos de Atendimento Oficial",
            url: "https://aima.gov.pt",
            icone: "🌐"
        },
        {
            nome: "SEGURANÇA SOCIAL DIRETA",
            categoria: "documentos",
            categoriaTexto: "Segurança Social & NISS",
            endereco: "Serviços de Atendimento da Segurança Social / NISS na Hora",
            url: "https://www.seg-social.pt/consultas/ss_direta/",
            icone: "🤝"
        },
        {
            nome: "PORTAL DO UTENTE SNS (SERVIÇO NACIONAL DE SAÚDE)",
            categoria: "saude-fiscal",
            categoriaTexto: "Saúde Pública",
            endereco: "Centros de Saúde Locais / Unidades de Saúde Familiar (USF)",
            url: "https://www.sns.gov.pt",
            icone: "🏥"
        }
    ];

    // CONTEÚDOS DOS TEXTOS DOS CARDS EMBALADOS NA CLASSE CORRETA
    const conteudosGuias = {
        nif: `
            <div class="guia-texto-container">
                <h3>Como obter o NIF e o NISS</h3>
                <p>O NIF e o NISS são os pilares essenciais para trabalhar e viver legalmente em Portugal.</p>
                <ul>
                    <li><strong>NIF:</strong> Solicita-se num balcão das Finanças ou Loja do Cidadão portando o passaporte válido.</li>
                    <li><strong>NISS:</strong> Pode ser obtido online através do serviço "NISS na Hora" no portal da Segurança Social.</li>
                </ul>
            </div>
        `,
        saude: `
            <div class="guia-texto-container">
                <h3>Acesso ao Serviço Nacional de Saúde (SNS)</h3>
                <p>Para ter acesso a consultas e assistência médica pública, deve registar-se no Centro de Saúde da sua área de residência.</p>
                <ul>
                    <li>Leve o seu passaporte, NIF e o seu comprovativo de morada oficial da Junta de Freguesia.</li>
                </ul>
            </div>
        `,
        aima: `
            <div class="guia-texto-container">
                <h3>AIMA e Fluxos de Regularização (2026)</h3>
                <p>A Agência para a Integração, Migrações e Asilo (AIMA) superintende os vistos e as autorizações de residência.</p>
                <p>Com as regras correntes vigentes para o ano de 2026, os processos dependem obrigatoriamente de agendamentos e canais de entrada eletrónicos controlados na plataforma oficial.</p>
            </div>
        `,
        equivalencias: `
            <div class="guia-texto-container">
                <h3>Validação e Equivalência de Diplomas</h3>
                <p>O processo para conferir validade jurídica aos seus estudos realizados fora de Portugal divide-se em duas frentes:</p>
                <ul>
                    <li><strong>Ensino Secundário:</strong> Tratado presencialmente num agrupamento de escolas secundárias públicas da sua área de morada.</li>
                    <li><strong>Ensino Superior:</strong> Deve ser submetido digitalmente através do portal nacional da DGES.</li>
                </ul>
            </div>
        `
    };

    function renderizarServicos(dadosFiltrados) {
        servicesGridContainer.innerHTML = "";
        if (dadosFiltrados.length === 0) {
            servicesGridContainer.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 20px;">Nenhum portal oficial encontrado.</p>`;
            return;
        }
        dadosFiltrados.forEach(item => {
            servicesGridContainer.innerHTML += `
                <div class="service-item-card">
                    <div class="card-top-header">
                        <div class="card-avatar-box">${item.icone}</div>
                        <div class="card-headline-box">
                            <h4>${item.nome}</h4>
                            <div class="card-tag-category">• ${item.categoriaTexto}</div>
                        </div>
                    </div>
                    <div class="card-address-panel">
                        <div class="address-label">Atendimento / Âmbito</div>
                        <div class="address-value">${item.endereco}</div>
                    </div>
                    <a href="${item.url}" target="_blank" class="btn-visit-website">🌐 Ir para o Site Oficial</a>
                </div>
            `;
        });
    }

    function filtrarServicos() {
        const termoBusca = searchInput.value.toLowerCase().trim();
        const categoriaSelecionada = categorySelect.value;
        const resultado = dadosServicos.filter(item => {
            const bateTexto = item.nome.toLowerCase().includes(termoBusca);
            const bateCategoria = (categoriaSelecionada === "todos") || (item.categoria === categoriaSelecionada);
            return bateTexto && bateCategoria;
        });
        renderizarServicos(resultado);
    }

    searchInput.addEventListener("input", filtrarServicos);
    categorySelect.addEventListener("change", filtrarServicos);
    renderizarServicos(dadosServicos);

    function calcularCustoVida() {
        const alojamento = parseFloat(inputAlojamento.value) || 0;
        const alimentacao = parseFloat(inputAlimentacao.value) || 0;
        const transportes = parseFloat(inputTransportes.value) || 0;
        const extras = parseFloat(inputExtras.value) || 0;
        txtTotalCusto.textContent = Math.round(alojamento + alimentacao + transportes + extras);
    }

    inputAlojamento.addEventListener("input", calcularCustoVida);
    inputAlimentacao.addEventListener("input", calcularCustoVida);
    inputTransportes.addEventListener("input", calcularCustoVida);
    inputExtras.addEventListener("input", calcularCustoVida);
    calcularCustoVida();

    function adicionarMensagem(autor, texto, tipo) {
        const divMensagem = document.createElement("div");
        divMensagem.className = `message ${tipo}`;
        divMensagem.innerHTML = `<p><strong>${autor}:</strong> ${texto}</p>`;
        chatWindow.appendChild(divMensagem);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function enviarMensagem() {
        const mensagemUtilizador = inputChat.value.trim();
        if (mensagemUtilizador === "") return;

        adicionarMensagem("Tu", mensagemUtilizador, "user");
        inputChat.value = "";

        const indicadorPensar = document.createElement("div");
        indicadorPensar.className = "message system";
        indicadorPensar.id = "status-ia-temporario";
        indicadorPensar.innerHTML = `<p><strong>Assistente:</strong> A consultar bases legais...</p>`;
        chatWindow.appendChild(indicadorPensar);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const response = await fetch("https://portal-imigrante-pt.onrender.com/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: mensagemUtilizador })
            });
            const elementoTemp = document.getElementById("status-ia-temporario");
            if (elementoTemp) elementoTemp.remove();
            const dados = await response.json();
            adicionarMensagem("Assistente", dados.response, "system");
        } catch (error) {
            const elementoTemp = document.getElementById("status-ia-temporario");
            if (elementoTemp) elementoTemp.remove();
            adicionarMensagem("Assistente", "Lamento, erro ao conectar com o terminal Python.", "system");
        }
    }

    function abrirGuia(chave) {
        const conteudo = conteudosGuias[chave];
        if (conteudo) {
            corpoTextoGuia.innerHTML = conteudo;
            areaGuiaDinamico.style.display = "block";
            areaGuiaDinamico.scrollIntoView({ behavior: "smooth" });
        }
    }

    document.getElementById("card-nif").addEventListener("click", () => abrirGuia("nif"));
    document.getElementById("card-saude").addEventListener("click", () => abrirGuia("saude"));
    document.getElementById("card-aima").addEventListener("click", () => abrirGuia("aima"));
    document.getElementById("card-equivalencias").addEventListener("click", () => abrirGuia("equivalencias"));

    btnFecharGuia.addEventListener("click", () => {
        areaGuiaDinamico.style.display = "none";
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    btnEnviar.addEventListener("click", enviarMensagem);
    inputChat.addEventListener("keypress", (e) => { if (e.key === "Enter") enviarMensagem(); });
});
