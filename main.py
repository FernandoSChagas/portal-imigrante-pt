import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from tavily import TavilyClient

app = Flask(__name__)
# Permite que o teu site no GitHub Pages comunique com o servidor Render sem bloqueios de segurança
CORS(app, resources={r"/api/*": {"origins": "*"}})

# =====================================================================
# INICIALIZAÇÃO DAS APIS (VARIÁVEIS DE AMBIENTE DO RENDER)
# =====================================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    print("⚠️ AVISO: Certifica-te de que as chaves GROQ_API_KEY e TAVILY_API_KEY estão configuradas no Render!")

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Memória temporária em servidor para o Assistente Virtual
historico_sessoes = {}

# =====================================================================
# 1. ROTA: PLANTÃO DE NOTÍCIAS AO VIVO (INDEX.HTML)
# =====================================================================
@app.route('/api/noticias', methods=['GET'])
def obter_noticias_vivas():
    try:
        # Varredura focada no nicho de imigração em Portugal nas últimas 24 horas
        busca = tavily_client.search(
            query="imigração Portugal vistos AIMA autorização residência novidades",
            search_depth="basic",
            time_range="day",
            max_results=5
        )
        
        noticias_formatadas = []
        for item in busca.get('results', []):
            # Tenta identificar uma tag limpa com base no título ou URL
            titulo_lower = item.get('title', '').lower()
            tag = "Atualidade"
            if "aima" in titulo_lower: tag = "AIMA"
            elif "visto" in titulo_lower: tag = "Vistos"
            elif "governo" in titulo_lower or "lei" in titulo_lower: tag = "Legislação"
            
            noticias_formatadas.append({
                "titulo": item.get('title', 'Notícia de Última Hora'),
                "resumo": item.get('content', '')[:150] + "...",
                "url": item.get('url', '#'),
                "tag": tag
            })
            
        # Fallback caso a internet esteja muito parada no dia e o Tavily retorne vazio
        if not noticias_formatadas:
            noticias_formatadas = [
                {
                    "titulo": "AIMA reforça atendimento digital para agendamentos de vistos",
                    "resumo": "Novas plataformas digitais prometem acelerar a regularização de processos pendentes de manifestações de interesse antigas...",
                    "url": "https://www.aima.gov.pt",
                    "tag": "AIMA"
                },
                {
                    "titulo": "Consulados portugueses registam alta na procura por Visto de Trabalho",
                    "resumo": "Procura por vistos de residência e procura de trabalho em Portugal mantém tendência de alta no primeiro semestre deste ano...",
                    "url": "https://www.diariodenoticias.pt",
                    "tag": "Vistos"
                }
            ]
            
        return jsonify({"noticias": noticias_formatadas}), 200
        
    except Exception as e:
        print(f"Erro na rota de notícias: {e}")
        return jsonify({"erro": "Não foi possível carregar o plantão.", "noticias": []}), 500

# =====================================================================
# 2. ROTA: ASSISTENTE VIRTUAL COM MEMÓRIA (ASSISTENTE.HTML)
# =====================================================================
@app.route('/api/chat', methods=['POST'])
def processar_chat_ia():
    dados = request.get_json() or {}
    mensagem_utilizador = dados.get('message', '').strip()
    session_id = dados.get('session_id', 'sessao_geral')

    if not mensagem_utilizador:
        return jsonify({"response": "Por favor, escreve uma mensagem válida."}), 400

    # Inicializa o histórico da sessão do utilizador se não existir
    if session_id not in historico_sessoes:
        historico_sessoes[session_id] = [
            {
                "role": "system",
                "content": (
                    "Atue como o Imigrante AI, o assistente oficial do Portal Imigrante PT. "
                    "Seu objetivo é ajudar imigrantes com dúvidas de imigração, burocracias (NIF, NISS, "
                    "Vistos, AIMA, regras de nacionalidade de 7 anos) e dicas práticas de viagem e adaptação. "
                    "Seja sempre extremamente acolhedor, prático, direto e use o português corrente de Portugal "
                    "ou uma linguagem clara e acessível. Nunca invente leis; avise para consultar canais oficiais se necessário."
                )
            }
        ]

    # Adiciona a mensagem atual do utilizador à memória da sessão
    historico_sessoes[session_id].append({"role": "user", "content": mensagem_utilizador})

    # Mantém apenas as últimas 12 mensagens para evitar estouro de memória do servidor
    if len(historico_sessoes[session_id]) > 13:
        historico_sessoes[session_id] = [historico_sessoes[session_id][0]] + historico_sessoes[session_id][-12:]

    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=historico_sessoes[session_id],
            temperature=0.6,
            max_tokens=800
        )
        
        resposta_ia = completion.choices[0].message.content
        # Adiciona a resposta da IA à memória para a próxima pergunta saber o contexto
        historico_sessoes[session_id].append({"role": "assistant", "content": resposta_ia})
        
        return jsonify({"response": resposta_ia}), 200

    except Exception as e:
        print(f"Erro no motor Groq Chat: {e}")
        return jsonify({"response": "[Erro Interno]: O motor de inteligência falhou a responder. Tente novamente."}), 500

# =====================================================================
# 3. NOVA ROTA COMBINADA: DOSSIÊ + LEITURAS (GUIAS.HTML)
# =====================================================================
@app.route('/api/guias', methods=['POST'])
def obter_guias_regionais():
    dados = request.get_json() or {}
    regiao = dados.get('regiao', 'Norte de Portugal')
    
    # --- 1. CHAMADA AO GROQ PARA GERAR O RELATÓRIO DA IA ---
    prompt_guia = f"""
    Atue como um Especialista Sénior em Relocalização e Integração em Portugal.
    Gere um relatório estratégico, pragmático e direto para um imigrante sobre a região: {regiao}.
    
    O relatório deve conter estritamente estes tópicos formatados de forma clara (use marcadores rápidos):
    - 💰 Custo de Vida Médio (Análise sobre Arrendamento e Supermercado face ao salário mínimo português)
    - 💼 Principais Indústrias e Empregos (Mercados de trabalho mais ativos e onde há mais contratações nesta zona)
    - 🌤️ Clima e Adaptação Cultural (O que esperar do tempo e do ritmo da população local)
    - 💡 Dica Humana de Integração (Uma orientação humana e prática de acolhimento para quem acaba de aterrar)
    
    Seja focado em dados úteis, assertivo e acolhedor. Evite introduções longas.
    """
    
    guia_ia_texto = "Análise estratégica regional temporariamente indisponível."
    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt_guia}],
            temperature=0.3
        )
        guia_ia_texto = completion.choices[0].message.content
    except Exception as e:
        print(f"Erro no Groq Rota Guias: {e}")

    # --- 2. CHAMADA AO TAVILY PARA CAPTURAR LEITURAS E CUSTO DE VIDA VIVO ---
    artigos_resultados = []
    try:
        termo_busca = f"custo de vida morar em {regiao} portugal dicas habitação"
        busca_tavily = tavily_client.search(
            query=termo_busca,
            search_depth="basic",
            time_range="year",
            max_results=3
        )
        
        for resultado in busca_tavily.get('results', []):
            artigos_resultados.append({
                "titulo": resultado.get('title', 'Guia Complementar de Habitação'),
                "resumo": resultado.get('content', '')[:160] + "...",
                "url": resultado.get('url', '#')
            })
    except Exception as e:
        print(f"Erro no Tavily Rota Guias: {e}")

    # Se o Tavily não achar nada sobre a região, entrega um fallback seguro
    if not artigos_resultados:
        artigos_resultados = [
            {
                "titulo": f"Guia de Custo de Vida e Habitação em {regiao}",
                "resumo": "Uma análise detalhada sobre preços de arrendamento de quartos, apartamentos e despesas essenciais nas principais cidades desta zona...",
                "url": "https://www.idealista.pt/news/"
            }
        ]

    return jsonify({
        "guia_ia": guia_ia_texto,
        "artigos": artigos_resultados
    }), 200

# =====================================================================
# EXECUÇÃO DO SERVIDOR DO FLASK
# =====================================================================
if __name__ == '__main__':
    # O Render atribui uma porta dinâmica através da variável de ambiente PORT
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
