import os
import requests
import re
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
# ENDPOINT: MOTOR RSS SEGURO (SIC NOTÍCIAS & DN PORTUGAL)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    """Consome feeds oficiais de Portugal via Regex/String de forma blindada contra falhas de XML"""
    # URLs oficiais e atualizadas dos feeds estruturados
    FEEDS_RSS = [
        {"tag": "SIC Notícias", "url": "https://sicnoticias.pt/noticias/?service=rss"},
        {"tag": "DN Portugal", "url": "https://www.dn.pt/rss/ultimas.xml"}
    ]
    
    PALAVRAS_CHAVE = ["aima", "imigração", "imigrante", "visto", "residência", "nacionalidade", "leis", "portugal", "estrangeiro"]
    noticias_filtradas = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for feed in FEEDS_RSS:
        try:
            response = requests.get(feed["url"], headers=headers, timeout=5)
            if response.status_code != 200:
                continue
                
            # Extração segura por blocos <item> usando Regex para evitar quebras por XML mal formado
            items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)
            
            for item in items:
                # Extrai os campos limpando CDATA e tags comuns
                titulo_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
                link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
                desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                
                titulo = titulo_match.group(1) if titulo_match else ""
                url = link_match.group(1) if link_match else "#"
                resumo_bruto = desc_match.group(1) if desc_match else ""
                
                # Limpeza profunda de CDATA e Tags HTML vindas dos jornais
                titulo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo).strip()
                url = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', url).strip()
                if resumo_bruto:
                    resumo_bruto = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', resumo_bruto)
                    resumo_bruto = re.sub('<[^<]+?>', '', resumo_bruto).strip()
                
                texto_analise = (titulo + " " + (resumo_bruto or "")).lower()
                
                # Filtro por nicho
                if any(termo in texto_analise for termo in PALAVRAS_CHAVE):
                    resumo = resumo_bruto[:140] + "..." if resumo_bruto else "Aceda aos detalhes completos no artigo original do portal."
                    noticias_filtradas.append({
                        "titulo": titulo,
                        "resumo": resumo,
                        "url": url,
                        "tag": feed["tag"]
                    })
                    
                if len(noticias_filtradas) >= 6:
                    break
        except Exception:
            continue

    # Se encontramos notícias do nicho, retorna imediatamente
    if len(noticias_filtradas) > 0:
        return {"noticias": noticias_filtradas[:5]}

    # FALLBACK REAL: Se não houver notícias de imigração nas últimas horas, 
    # extrai as últimas notícias gerais publicadas para manter o site sempre vivo
    try:
        noticias_fallback = []
        for feed in FEEDS_RSS:
            response = requests.get(feed["url"], headers=headers, timeout=4)
            items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)[:3]
            for item in items:
                titulo_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
                link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
                desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                
                t = titulo_match.group(1) if titulo_match else "Última Hora"
                u = link_match.group(1) if link_match else "#"
                d = desc_match.group(1) if desc_match else ""
                
                t = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', t).strip()
                u = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', u).strip()
                if d:
                    d = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', d)
                    d = re.sub('<[^<]+?>', '', d).strip()
                
                noticias_fallback.append({
                    "titulo": t,
                    "resumo": d[:130] + "..." if d else "Verifique a cobertura completa no portal oficial.",
                    "url": u,
                    "tag": feed["tag"]
                })
        if noticias_fallback:
            return {"noticias": noticias_fallback[:5]}
    except Exception:
        pass

    # BACKUP FIXO DE SEGURANÇA SE A REDE DE FEEDS CAIR POR COMPLETO
    return {
        "noticias": [
            {
                "titulo": "Plantão de Updates do Ecossistema",
                "resumo": "Acompanha os novos fluxos de triagem e tempos médios de resposta para vistos e agendamentos estruturados neste trimestre...",
                "url": "https://aima.gov.pt",
                "tag": "AIMA"
            },
            {
                "titulo": "Contagem de prazos para Nacionalidade",
                "resumo": "Análise detalhada sobre os critérios de fixação de residência legal efetiva para fins de attribution de cidadania portuguesa...",
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
                    "- A tua personalidade é acolhedora, prática e extremamente direta. Fala como um veterano objetivo.\n"
                    "- PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'de outras IAs' ou 'MIRA'.\n\n"
                    
                    "REGRA DE TRANSPARÊNCIA E DO ANO ATUAL:\n"
                    "- O ano atual é 2026.\n"
                    "- Se te perguntarem sobre notícias em tempo real deste mês, sê honesto e curto: explica que o teu foco é a estrutura legal estável (7 anos, AIMA, NIF) e sugere olhar o painel de notícias da nossa página inicial.\n\n"
                    
                    "ESCOPO DE ATUAÇÃO:\n"
                    "1. LOGÍSTICA DE VIAGem E VOOS: Passagens, malas de mão, conexões.\n"
                    "2. DICAS HUMANAS DE SOBREVIVÊNCIA: Mudança, custo de vida, quartos, adaptação cultural.\n"
                    "3. BUROCRACIA LEGAL: Regra de 7 ANOS de residência para nacionalidade via CPLP/UE (Lei de 2026), NIF, NISS e AIMA.\n\n"
                    
                    "REGRAS ESTRITAS DE FORMATO:\n"
                    "- Responde à pergunta logo na primeira frase.\n"
                    "- O limite máximo absoluto de cada resposta é de 2 parágrafos curtos.\n"
                    "- Em locais de lista, usa unicamente hifens (-) e no máximo 3 a 4 pontos."
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
