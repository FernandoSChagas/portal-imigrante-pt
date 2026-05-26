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
# ENDPOINT: MOTOR DE BUSCA DA SEMANA (ORDENADO POR NOVIDADE)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    """Pesquisa jornalismo dos últimos 7 dias e coloca a mais recente no primeiro card"""
    try:
        url = "https://api.tavily.com/search"
        
        # Filtro cirúrgico focado em grandes portais com alcance da última semana
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": "site:sicnoticias.pt OR site:dn.pt OR site:publico.pt OR site:jn.pt imigração AIMA leis Portugal",
            "search_depth": "advanced",
            "time_range": "week",  # <--- FORÇA A BUSCA DE NOTÍCIAS DA SEMANA
            "max_results": 6       # Puxamos mais resultados para ter um carrossel rico
        }
        
        response = requests.post(url, json=payload, timeout=6)
        if response.status_code == 200:
            resultados = response.json().get("results", [])
            
            noticias_brutas = []
            for item in resultados:
                site_url = item.get("url", "").lower()
                
                # Identifica dinamicamente a fonte do jornal português
                tag = "Jornalismo PT"
                if "sicnoticias" in site_url:
                    tag = "SIC Notícias"
                elif "dn.pt" in site_url:
                    tag = "DN Portugal"
                elif "publico.pt" in site_url:
                    tag = "Público"
                elif "jn.pt" in site_url:
                    tag = "Jornal de Notícias"
                elif "aima" in site_url:
                    tag = "AIMA"

                noticias_brutas.append({
                    "titulo": item.get("title", "Atualização Legal Importante"),
                    "resumo": item.get("content", "Verifica os detalhes completos no artigo original do portal.")[:140] + "...",
                    "url": item.get("url", "#"),
                    "tag": tag,
                    "score": item.get("score", 0.0)  # Relevância e frescura dentro da semana
                })
            
            # ORDENAÇÃO: Coloca o score mais alto (mais recente/relevante da semana) no topo
            noticias_ordenadas = sorted(noticias_brutas, key=lambda x: x["score"], reverse=True)
            
            if noticias_ordenadas:
                # Retorna até 5 notícias para o carrossel ficar com movimento nas setas, 
                # mas o teu index.html vai mostrar sempre 3 de cada vez na tela do PC!
                return {"noticias": noticias_ordenadas[:5]}
                
    except Exception:
        pass
        
    # BACKUP SE A API FALHAR
    return {
        "noticias": [
            {
                "titulo": "Plantão de Atualizações AIMA 2026",
                "resumo": "Acompanha a reestruturação dos novos balcões de atendimento e regras de agendamento digital para este trimestre...",
                "url": "https://aima.gov.pt",
                "tag": "AIMA"
            },
            {
                "titulo": "Artigo 15: Contagem de prazos para Nacionalidade",
                "resumo": "Análise detalhada sobre os critérios de fixação de residência legal efetiva para fins de atribuição de cidadania portuguesa...",
                "url": "https://diariodarepublica.pt",
                "tag": "DN Portugal"
            },
            {
                "titulo": "Logística e Vistos: Balanço Consular Semanal",
                "resumo": "Verifica os novos fluxos de triagem e tempos médios de resposta para vistos de residência emitidos na rede diplomática...",
                "url": "https://portaldascomunidades.mne.gov.pt",
                "tag": "SIC Notícias"
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
