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

# Puxa as chaves guardadas nas variáveis de ambiente do Render
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "") # Configura esta chave no Render para ativar a busca ao vivo

client = Groq(api_key=GROQ_API_KEY)

# Memória global do chat por sessão
historico_conversas = {}

class UserMessage(BaseModel):
    message: str
    session_id: str = "comum"

# =====================================================================
# ENDPOINT: MOTOR DE NOTÍCIAS EM TEMPO REAL PARA O HUB
# =====================================================================
@app.get("/api/noticias")
async def obter_noticias_tempo_real():
    """Pesquisa na internet pelas regras, avisos e notícias mais recentes de imigração em Portugal"""
    if not TAVILY_API_KEY:
        # Se não houver chave Tavily configurada, retorna uma lista padrão para o feed não ficar vazio
        return {
            "noticias": [
                {
                    "titulo": "Avisos Recentes AIMA 2026",
                    "resumo": "Consulta os novos canais digitais oficiais para o agendamento de manifestações de interesse e regularização de vistos diretamente no portal.",
                    "url": "https://aima.gov.pt"
                },
                {
                    "titulo": "Contagem de Tempo de Residência (7 Anos)",
                    "resumo": "As regras de nacionalidade vigentes consolidam os prazos legais de residência para cidadãos da CPLP e União Europeia.",
                    "url": "https://diariodarepublica.pt"
                }
            ]
        }
        
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": "noticias AIMA leis imigração Portugal avisos recentes 2026",
            "search_depth": "advanced",
            "max_results": 3
        }
        response = requests.post(url, json=payload, timeout=6)
        if response.status_code == 200:
            resultados = response.json().get("results", [])
            
            noticias_formatadas = []
            for item in resultados:
                noticias_formatadas.append({
                    "titulo": item.get("title", "Atualização Legal Importante"),
                    "resumo": item.get("content", "Verifica os detalhes completos no artigo original do portal.")[:160] + "...",
                    "url": item.get("url", "#")
                })
            return {"noticias": noticias_formatadas}
    except Exception:
        pass
        
    return {"noticias": []}

# =====================================================================
# ENDPOINT DO CHAT: ASSISTENTE IA COM MEMÓRIA HUMANA
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
                    "- Em internacionais listas, usa unicamente hifens (-) e no máximo 3 a 4 pontos."
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
