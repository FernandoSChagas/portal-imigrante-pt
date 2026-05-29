import os
import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - IA Humana e Abrangente")

# Configuração de CORS para o teu link do GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Puxa a chave da Groq guardada no Render
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)

historico_conversas = {}

class UserMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def responder_chat(user_data: UserMessage):
    mensagem_utilizador = user_data.message
    sessao_id = "utilizador_atual"
    
    if sessao_id not in historico_conversas:
        historico_conversas[sessao_id] = [
            {
                "role": "system",
                "content": (
                    "PROVÍNCIA, IDENTIDADE E PERSONALIDADE:\n"
                    "- Tu és o IMIGRANTE AI, o assistente virtual oficial e conselheiro humano do Portal Imigrante PT.\n"
                    "- A tua personalidade é acolhedora, prática, experiente e muito realista. Tu falas como um imigrante veterano que já passou por tudo e quer ajudar um recém-chegado.\n"
                    "- PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'MIRA'.\n\n"
                    
                    "ESCOPO DE ATUAÇÃO ABRANGENTE (SABER SOBRE TUDO):\n"
                    "Tu deves responder com propriedade sobre três grandes pilares:\n"
                    "1. LOGÍSTICA DE VIAGEM E VOOS: Dicas sobre escolha de passagens, controlo de bagagem, conexões e escalas em aeroportos, direitos do passageiro e organização de documentos de viagem.\n"
                    "2. DICAS HUMANAS E REAIS DE SOBREVIVÊNCIA: Como é o processo psicológico da mudança, como fazer as primeiras compras de supermercado, como funciona o arrendamento real (e a procura de quartos), o clima nas diferentes estações, e como se adaptar à cultura local.\n"
                    "3. BUROCRACIA LEGAL: Mantém a regra dos 7 anos de residência legal para nacionalidade via CPLP/UE (Lei de 2026), NIF, NISS e papel da AIMA.\n\n"
                    
                    "TONALIDADE E REGRAS DE RESPOSTA:\n"
                    "- Junta conselhos práticos às respostas burocráticas. Se te perguntarem sobre o Porto ou Guimarães, fala sobre os transportes locais ou o custo prático da zona.\n"
                    "- Sê extremamente direto. Responde logo no primeiro parágrafo.\n"
                    "- Mantém as respostas curtas e fáceis de ler no telemóvel (máximo 3 parágrafos).\n"
                    "- Para listas, usa unicamente o hífen (-) como marcador (limite de 5 pontos)."
                )
            }
        ]
    
    historico_conversas[sessao_id].append({"role": "user", "content": mensagem_utilizador})
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=historico_conversas[sessao_id],
            temperature=0.4
        )
        resposta_final = completion.choices[0].message.content
        historico_conversas[sessao_id].append({"role": "assistant", "content": resposta_final})
    except Exception as e:
        resposta_final = f"[Erro de Conexão]: Ocorreu um problema no motor inteligente. Detalhe: {str(e)}"

    return {"response": resposta_final}

# =====================================================================
# ROTA DE NOTÍCIAS BLINDADA (RSS INDEPENDENTE VIA PYTHON)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    fontes_rss = [
        {"url": "https://www.dn.pt/rss/portugal.xml", "tag": "DN Portugal"},
        {"url": "https://sicnoticias.pt/rss", "tag": "SIC Notícias"},
        {"url": "https://rss.rtp.pt/noticias/index.xml", "tag": "RTP Notícias"},
        {"url": "https://www.publico.pt/feed/ultimo", "tag": "Público"}
    ]
    noticias_brutas = []
    img_placeholder = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop"

    # Rodamos cada fonte dentro de um bloco try/except isolado
    for fonte in fontes_rss:
        try:
            feed = feedparser.parse(fonte["url"])
            if not feed.entries:
                continue
                
            for entry in feed.entries[:3]:
                img_url = img_placeholder
                if 'media_content' in entry and len(entry.media_content) > 0:
                    img_url = entry.media_content[0].get('url', img_placeholder)
                elif 'links' in entry:
                    for link in entry.links:
                        if 'image' in link.get('type', ''):
                            img_url = link.get('href', img_placeholder)
                elif 'enclosure' in entry:
                    img_url = entry.enclosure.get('url', img_placeholder)

                resumo_limpo = entry.get("summary", "Acompanhe os detalhes da atualização no artigo completo.")
                if resumo_limpo and "<" in resumo_limpo:
                    resumo_limpo = resumo_limpo.split("<")[0]
                
                if not resumo_limpo or len(resumo_limpo.strip()) < 10:
                    resumo_limpo = "Clique para ler os detalhes completos da atualização oficial em Portugal."

                noticias_brutas.append({
                    "titulo": entry.get("title", ""),
                    "resumo": resumo_limpo[:110] + "...",
                    "url": entry.get("link", "#"),
                    "tag": fonte["tag"],
                    "imagem": img_url
                })
        except Exception as e:
            print(f"Erro temporário na fonte {fonte['tag']}: {e}")
            continue

    # Remove duplicados por título
    noticias_limpas = []
    vistas = set()
    for n in noticias_brutas:
        if n["titulo"] not in vistas:
            vistas.add(n["titulo"])
            noticias_limpas.append(n)

    # Injeta o teu e-book SEMPRE na terceira posição (índice 2)
    noticias_limpas.insert(2, {
        "titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal",
        "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro para proteger a poupança inicial...",
        "url": "viver-do-digital.html",
        "tag": "Tendência",
        "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
    })

    # Caso todas as fontes falhem, garante ao menos estes fallbacks com o e-book
    if len(noticias_limpas) < 3:
        noticias_limpas.append({
            "titulo": "AIMA otimiza plataforma digital para atualização de processos",
            "resumo": "Nova atualização pretende agilizar a validação de dados de manifestações de interesse antigas...",
            "url": "https://aima.gov.pt",
            "tag": "AIMA Oficial",
            "imagem": "https://images.unsplash.com/photo-1450133064473-71024230f91b?q=80&w=600&auto=format&fit=crop"
        })
        noticias_limpas.append({
            "titulo": "Segurança Social adota novo sistema de agendamento para o NISS",
            "resumo": "Medida visa reduzir as filas de espera e facilitar a atribuição do número para novos residentes estrangeiros...",
            "url": "https://www.seg-social.pt",
            "tag": "Segurança Social",
            "imagem": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?q=80&w=600&auto=format&fit=crop"
        })

    return {"noticias": noticias_limpas[:10]}

@app.get("/")
def home():
    return {"status": "Servidor com IA abrangente de viagens e sobrevivência humana online!"}
