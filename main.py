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
# ENDPOINT: MOTOR RSS INTELIGENTE EM TEMPO REAL DIRECTO DOS JORNAIS
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    """Consome feeds RSS oficiais de Portugal em tempo real e filtra por termos de imigração"""
    # Feeds RSS estáveis de notícias gerais de última hora em Portugal
    FEEDS_RSS = [
        {"tag": "Jornal de Notícias", "url": "https://www.jn.pt/rss/ultimas.xml"},
        {"tag": "Público", "url": "https://www.publico.pt/feed/ultimas"}
    ]
    
    # Palavras-chave cirúrgicas para o filtro do Portal Imigrante PT
    PALAVRAS_CHAVE = ["aima", "imigração", "imigrante", "visto", "residência", "nacionalidade", "leis", "portugal", "estrangeiro"]
    
    noticias_filtradas = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for feed in FEEDS_RSS:
        try:
            # Requisição direta do servidor (ignora o bloqueio de CORS dos navegadores)
            response = requests.get(feed["url"], headers=headers, timeout=4)
            if response.status_code != 200:
                continue
                
            # Processamento da árvore estrutural do XML
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item'):
                titulo = item.find('title').text if item.find('title') is not None else ""
                resumo_bruto = item.find('description').text if item.find('description') is not None else ""
                url = item.find('link').text if item.find('link') is not None else "#"
                
                # Tratamento de limpeza simples para descrições com tags HTML perdidas no RSS
                if resumo_bruto and "<" in resumo_bruto:
                    resumo_bruto = ET.fromstring(f"<span>{resumo_bruto}</span>").text or resumo_bruto
                
                texto_analise = (titulo + " " + (resumo_bruto or "")).lower()
                
                # Executa o filtro inteligente: valida se a notícia é de interesse do seu público
                if any(termo in texto_analise for termo in PALAVRAS_CHAVE):
                    resumo = resumo_bruto[:140] + "..." if resumo_bruto else "Aceda aos detalhes completos no artigo original do portal."
                    
                    noticias_filtradas.append({
                        "titulo": titulo,
                        "resumo": resumo,
                        "url": url,
                        "tag": feed["tag"]
                    })
                    
                # Break de segurança para não processar dados em excesso e manter a rota ultra-rápida
                if len(noticias_filtradas) >= 8:
                    break
                    
        except Exception:
            continue # Se um feed falhar isoladamente, passa para o próximo sem quebrar a API

    # Se o filtro encontrou notícias quentes de hoje, envia para o carrossel
    if len(noticias_filtradas) > 0:
        return {"noticias": noticias_filtradas[:5]}

    # FALLBACK INTELIGENTE: Se nenhum jornal publicou sobre imigração nas últimas horas,
    # o servidor entrega as notícias gerais mais recentes dos feeds para o carrossel nunca ficar vazio.
    try:
        response = requests.get(FEEDS_RSS[0]["url"], headers=headers, timeout=3)
        root = ET.fromstring(response.content)
        for item in root.findall('.//item')[:3]:
            noticias_filtradas.append({
                "titulo": item.find('title').text,
                "resumo": (item.find('description').text or "")[:140] + "...",
                "url": item.find('link').text,
                "tag": FEEDS_RSS[0]["tag"]
            })
        return {"noticias": noticias_filtradas}
    except Exception:
        pass

    # BACKUP FIXO DE SEGURANÇA ABSOLUTA CASO TODA A REDE FALHE
    return {
        "noticias": [
            {
                "titulo": "Plantão de Atualizações AIMA",
                "resumo": "Acompanha a reestruturação dos novos balcões de atendimento e regras de agendamento digital para este trimestre...",
                "url": "https://aima.gov.pt",
                "tag": "AIMA"
            },
            {
                "titulo": "Contagem de prazos para Nacionalidade",
                "resumo": "Análise detalhada sobre os critérios de fixação de residência legal efetiva para fins de atribuição de cidadania portuguesa...",
                "url": "https://diariodarepublica.pt",
                "tag": "DN Portugal"
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
                    "- A tua personalidade é acolhedora, prática e extremamente direta. Fala como um veterano objective.\n"
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
