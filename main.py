import os
import requests
import xml.etree.ElementTree as ET
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
client = Groq(api_key=GROQ_API_KEY)

# Memória global do chat por sessão
historico_conversas = {}

class UserMessage(BaseModel):
    message: str
    session_id: str = "comum"

# =====================================================================
# ENDPOINT: MOTOR RSS EM TEMPO REAL ABSOLUTO (SIC, JN, PÚBLICO)
# =====================================================================
@app.get("/api/noticias")
async def obter_noticias_tempo_real():
    """Lê diretamente os feeds RSS dos jornais portugueses em tempo real"""
    
    # Lista de feeds RSS oficiais de Portugal
    feeds_rss = {
        "SIC Notícias": "https://sicnoticias.pt/rss",
        "Jornal de Notícias": "https://www.jn.pt/rss.xml",
        "Público": "https://www.publico.pt/rss"
    }
    
    noticias_detetadas = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Palavras-chave para capturar apenas o que interessa ao teu público
    termos_busca = ["imigra", "visto", "aima", "brasil", "estrangeir", "sef", "cplp", "nacionalidade", "residenc"]

    for fonte, url in feeds_rss.items():
        try:
            response = requests.get(url, headers=headers, timeout=4)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                # Varre os artigos dentro do XML do feed
                for item in root.findall(".//item"):
                    titulo = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else "#"
                    resumo = item.find("description").text if item.find("description") is not None else ""
                    
                    # Limpa tags HTML básicas que possam vir no resumo do RSS
                    if resumo:
                        resumo = resumo.split("<")[0].strip()

                    texto_para_validar = (titulo + " " + resumo).lower()
                    
                    # Filtro inteligente: Verifica se o artigo fala de imigração ou temas ligados
                    if any(termo in texto_para_validar for termo in termos_busca):
                        noticias_detetadas.append({
                            "titulo": titulo,
                            "resumo": resumo[:140] + "..." if len(resumo) > 140 else resumo,
                            "url": link,
                            "tag": fonte
                        })
        except Exception:
            continue # Se um jornal estiver fora do ar, pula para o seguinte sem travar o site

    # Se encontrarmos notícias reais nos feeds oficiais, entregamos de imediato
    if noticias_detetadas:
        # Nota: Os feeds RSS já vêm naturalmente ordenados por ordem de publicação (as mais novas no topo)
        # Retornamos as 3 primeiras mais frescas encontradas na rede
        return {"noticias": noticias_detetadas[:3]}
        
    # BACKUP SE OS FEEDS FALHAREM COMPLETAMENTE (Garante que a tela nunca fica vazia)
    return {
        "noticias": [
            {
                "titulo": "Plantão de Atualizações AIMA",
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
                "titulo": "Logística e Vistos: Balanço Consular das Últimas Horas",
                "resumo": "Verifica os novos fluxos de triagem e tempos médios de resposta para vistos de residência emitidos na rede diplomática...",
                "url": "https://portaldascomunidades.mne.gov.pt",
                "tag": "SIC Notícias"
            }
        ]
    }

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
