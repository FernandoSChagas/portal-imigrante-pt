import os
import feedparser
import requests
from bs4 import BeautifulSoup
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
                    "- A tua personalidade é acolhedora, practical, experiente e muito realista. Tu falas como um imigrante veterano que já passou por tudo e quer ajudar um recém-chegado.\n"
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

# Função interna para varrer o site do jornal e capturar a imagem de destaque real
def extrair_imagem_real(url_artigo, placeholder):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        # Faz uma requisição rápida para não travar o carregamento do carrossel
        r = requests.get(url_artigo, headers=headers, timeout=2)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Captura a tag que guarda a imagem principal da notícia
            meta_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_img and meta_img.get("content"):
                return meta_img["content"]
    except:
        pass
    return placeholder

# =====================================================================
# ROTA DE NOTÍCIAS AUTOMÁTICA (INTEGRAÇÃO COMPLETA GOOGLE NEWS + IMAGENS)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    # Agregador configurado para colher atualizações da SIC e DN sem sofrer bloqueios de rede
    url_google_news = "https://news.google.com/rss/search?q=imigra%C3%A7%C3%A3o+portugal+site:sicnoticias.pt+OR+site:dn.pt&hl=pt-PT&gl=PT&ceid=PT:pt-pt"
    
    noticias_final = []
    img_placeholder = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop"

    try:
        feed = feedparser.parse(url_google_news)
        
        # Filtra as 5 notícias mais recentes publicadas
        for entry in feed.entries[:5]:
            titulo = entry.get("title", "")
            if " - " in titulo:
                titulo = titulo.split(" - ")[0] # Remove o nome do jornal anexado pelo Google no fim do título

            link_original = entry.get("link", "#")
            
            # Identificação dinâmica da Tag do Card
            tag = "Portugal"
            if "sicnoticias" in link_original.lower(): tag = "SIC Notícias"
            elif "dn.pt" in link_original.lower(): tag = "DN Portugal"

            # Executa a varredura em segundo plano para extrair a foto real da notícia
            imagem_capa = extrair_imagem_real(link_original, img_placeholder)

            noticias_final.append({
                "titulo": titulo,
                "resumo": "Clique no link abaixo para acompanhar a cobertura completa desta atualização diretamente no portal oficial.",
                "url": link_original,
                "tag": tag,
                "imagem": imagem_capa
            })
    except Exception as e:
        print(f"Erro ao processar agregador: {e}")

    # Injeta a estratégia do seu e-book de negócios digitais perfeitamente na 3ª posição
    noticias_final.insert(2, {
        "titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal",
        "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro para proteger a poupança inicial...",
        "url": "viver-do-digital.html",
        "tag": "Tendência",
        "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
    })

    # Backup caso o agregador falhe e o carrossel precise de dados mínimos
    if len(noticias_final) < 2:
        noticias_final.append({
            "titulo": "AIMA otimiza plataforma digital para atualização de processos",
            "resumo": "Nova atualização pretende agilizar a validação de dados de manifestações de interesse antigas...",
            "url": "https://aima.gov.pt",
            "tag": "AIMA Oficial",
            "imagem": "https://images.unsplash.com/photo-1450133064473-71024230f91b?q=80&w=600&auto=format&fit=crop"
        })

    return {"noticias": noticias_final[:10]}

@app.get("/")
def home():
    return {"status": "Servidor com IA abrangente de viagens e sobrevivência humana online!"}
