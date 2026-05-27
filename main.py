import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - Ecossistema Unificado")

# Configuração de CORS aberta para permitir que o teu GitHub Pages aceda com segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chaves de API estáveis do ecossistema
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
TAVILY_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# Memória global do chat por sessão
historico_conversas = {}

class UserMessage(BaseModel):
    message: str
    session_id: str = "comum"

# =====================================================================
# ENDPOINT: NOVO MOTOR DE BUSCA GLOBAL E MULTI-FONTE (TEMPO REAL)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    """Pesquisa em tempo real por todo o universo de imigração, vistos e viagens em múltiplos jornais"""
    try:
        url = "https://api.tavily.com/search"
        
        # Query expandida e refinada para cruzar termos do ecossistema luso-brasileiro
        query_global = (
            "imigração Portugal AIMA vistos passaporte autorização de residência "
            "leis voos viagens cartão cidadão Polícia Federal Consulado hoje últimas notícias"
        )
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query_global,
            "search_depth": "advanced",
            "time_range": "day",  # <--- LIMITA RIGOROSAMENTE ÀS ÚLTIMAS 24 HORAS
            "max_results": 8      # Puxamos mais resultados para ter um filtro de fontes mais rico
        }
        
        response = requests.post(url, json=payload, timeout=6)
        if response.status_code == 200:
            resultados = response.json().get("results", [])
            
            noticias_brutas = []
            for item in resultados:
                site_url = item.get("url", "").lower()
                titulo = item.get("title", "")
                
                # Sistema dinâmico e inteligente para detetar e rotular a fonte original da notícia
                tag = "Atualidade"
                if "sicnoticias" in site_url:
                    tag = "SIC Notícias"
                elif "dn.pt" in site_url or "dn-pt" in site_url:
                    tag = "DN Portugal"
                elif "publico" in site_url:
                    tag = "Público"
                elif "jn.pt" in site_url:
                    tag = "Jornal de Notícias"
                elif "aima" in site_url:
                    tag = "AIMA Oficial"
                elif "g1" in site_url or "globo" in site_url:
                    tag = "G1 Brasil"
                elif "cnn" in site_url:
                    tag = "CNN"
                elif "rtp" in site_url:
                    tag = "RTP Notícias"
                elif "observador" in site_url:
                    tag = "Observador"
                elif "gov.br" in site_url or "pf.gov.br" in site_url:
                    tag = "Gov Brasil"
                elif "consulado" in site_url:
                    tag = "Consular"
                elif "diariodarepublica" in site_url:
                    tag = "Diário da República"
                elif ".br" in site_url:
                    tag = "Plantão BR"
                elif ".pt" in site_url:
                    tag = "Plantão PT"

                # Ignora páginas institucionais vazias ou termos repetitivos na home
                if "justiça" in titulo.lower() and len(titulo) < 15:
                    continue

                noticias_brutas.append({
                    "titulo": titulo,
                    "resumo": item.get("content", "Aceda à cobertura de última hora diretamente no portal de notícias mapeado.")[:135] + "...",
                    "url": item.get("url", "#"),
                    "tag": tag
                })
            
            if noticias_brutas:
                # Retorna os 5 resultados mais quentes encontrados na internet nas últimas 24h
                return {"noticias": noticias_brutas[:5]}
                
    except Exception:
        pass
        
    # BACKUP SE A API TAVILY CAIR (Garante que o carrossel nunca fique em branco)
    return {
        "noticias": [
            {
                "titulo": "Plantão Consular: Emissão de Passaportes e Vistos",
                "resumo": "Acompanha os fluxos de triagem, taxas consulares e prazos de entrega para os novos vistos de procura de trabalho e residência...",
                "url": "https://portaldascomunidades.mne.gov.pt",
                "tag": "Consular"
            },
            {
                "titulo": "Reestruturação de Agendamentos e Cartões AIMA",
                "resumo": "Novas diretivas para a validação de processos pendentes, renovações automáticas e agendamento de manifestações de interesse...",
                "url": "https://aima.gov.pt",
                "tag": "AIMA Oficial"
            },
            {
                "titulo": "Contagem de Prazos Legais para Cidadania Europeia",
                "resumo": "Análise sobre a fixação do tempo de residência legal efetiva sob o abrigo das novas emendas à Lei da Nacionalidade...",
                "url": "https://diariodarepublica.pt",
                "tag": "Leis PT"
            }
        ]
    }

# =====================================================================
# ENDPOINT DO CHAT: ASSISTENTE IA WITH HUMAN MEMORY
# =====================================================================
@app.post("/api/chat")
async def responder_chat(user_data: UserMessage):
    mensagem_utilizador = user_data.message
    sessao_id = user_data.session_id 
    
    if sessao_id not in historico_conversas:
        historico_conversas[sessao_id] = [
            {
                "role": "system",
                "content": (
                    "PROVÍNCIA, IDENTIDADE E PERSONALIDADE:\n"
                    "- Tu és o IMIGRANTE AI, o assistente virtual oficial do Portal Imigrante PT.\n"
                    "- Tu tens uma MEMÓRIA HUMANA: lembra-te do nome do utilizador e do contexto que ele já partilhou contigo ao longo do diálogo.\n"
                    "- A tua personalidade é acolhedora, prática e extremamente direta. Fala como um veterano objetivo.\n"
                    "- PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'de outras IAs' ou 'MIRA'.\n\n"
                    
                    "REGRA DE TRANSPARÊNCIA E DO ANO ATUAL:\n"
                    "- O ano atual é 2026.\n"
                    "- Se te perguntarem sobre notícias em tempo real deste mês, sê honesto e curto: explica que o teu foco é a estrutura legal estável (7 anos, AIMA, NIF) e sugere olhar o painel de notícias da nossa página inicial.\n\n"
                    
                    "ESCOPO DE ATUAÇÃO:\n"
                    "1. LOGÍSTICA DE VIAGEM E VOOS: Passagens, malas de mão, conexões.\n"
                    "2. DICAS HUMANAS DE SOBREVIVÊNCIA: Mudança, custo de vida, quartos, adaptação cultural.\n"
                    "3. BUROCRACIA LEGAL: Regra de 7 ANOS de residência para nacionalidade via CPLP/UE (Lei de 2026), NIF, NISS e AIMA.\n\n"
                    
                    "REGRAS ESTRITAS DE FORMATO:\n"
                    "- Responde à pergunta logo na primeira frase.\n"
                    "- O limite máximo absoluto de cada resposta é de 2 parágrafos curtos.\n"
                    "- Em listas, usa unicamente hifens (-) e no máximo 3 a 4 pontos."
                )
            }
        ]
    
    historico_conversas[sessao_id].append({"role": "user", "content": mensagem_utilizador})
    
    if len(historico_conversas[sessao_id]) > 13:
        system_prompt = historico_conversas[sessao_id][0]
        historico_conversas[sessao_id] = [system_prompt] + historico_conversas[sessao_id][-12:]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=historico_conversas[sessao_id],
            temperature=0.2
        )
        resposta_final = completion.choices[0].message.content
        historico_conversas[sessao_id].append({"role": "assistant", "content": resposta_final})
    except Exception as e:
        resposta_final = f"[Erro de Conexão]: Ocorreu um problema no motor inteligente. Detalhe: {str(e)}"

    return {"response": resposta_final}

@app.get("/")
def home():
    return {"status": "Servidor do Ecossistema Portal Imigrante PT Online!"}
