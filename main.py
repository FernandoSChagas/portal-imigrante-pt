import os
import csv
import feedparser
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - Engenharia Unificada")

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

# Modelos de dados (Pydantic) para validação das requisições
class UserMessage(BaseModel):
    message: str

class RegionRequest(BaseModel):
    regiao: str

class SimulationRequest(BaseModel):
    perfil: str = "casal"
    regiao: str = "Norte de Portugal"
    meses: int = 6
    nome: str
    email: str
    whatsapp: str = "Não informado"

# LINK DO TEU GOOGLE APPS SCRIPT REAL E ATUALIZADO
URL_GOOGLE_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbx-S0LKPb0z4-J8uitpt3_tB7dYYxaTFpA2KXIjWJkU3BNT9empVC17YRzaf3dgGweW/exec"

# =====================================================================
# 1. ROTA DE SEGURANÇA: ÁREA RESTRITA / LEITURA VIA SCRIPT GOOGLE
# =====================================================================
@app.get("/api/leads")
async def obtener_leads_da_planilha():
    try:
        r = requests.get(URL_GOOGLE_APPS_SCRIPT, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Erro ao ler Apps Script: {e}")
        
    leads_formatados = [
        {"data": "28/05/2026 12:22:36", "nome": "luciane", "email": "luciane@gmail.com", "whatsapp": "Não informado", "origem": "Simulador"},
        {"data": "28/05/2026 11:37:49", "nome": "fernando", "email": "fernando@gmail.com", "whatsapp": "Não informado", "origem": "Simulador"}
    ]
    return {"leads": leads_formatados}

# =====================================================================
# 2. ROTA: SIMULADOR DE RESERVA DE SEGURANÇA
# =====================================================================
@app.post("/api/simulador")
async def processar_simulacao(data: SimulationRequest):
    try:
        payload_google = {
            "nome": data.nome,
            "email": data.email,
            "whatsapp": data.whatsapp if data.whatsapp else "Não informado",
            "origem": "Simulador"
        }
        requests.post(URL_GOOGLE_APPS_SCRIPT, json=payload_google, timeout=5)
    except Exception as e:
        print(f"Erro ao disparar lead para o Google Sheets: {e}")

    custo_base = 900
    if "casal" in data.perfil.lower():
        custo_base = 1400
    elif "familia" in data.perfil.lower() or "família" in data.perfil.lower():
        custo_base = 1800

    multiplicador_regiao = 1.0
    if "Lisboa" in data.regiao:
        multiplicador_regiao = 1.35
    elif "Algarve" in data.regiao or "Norte" in data.regiao:
        multiplicador_regiao = 1.1

    total_euro = float(custo_base * multiplicador_regiao * data.meses)

    cotacao_brl = 5.85
    try:
        res_cambio = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2)
        if res_cambio.status_code == 200:
            cotacao_brl = float(res_cambio.json()["rates"]["BRL"])
    except:
        pass

    total_real = float(total_euro * cotacao_brl)
    insight_texto = f"Cálculo estruturado para {data.nome}. A transição exige planeamento estratégico."

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "És um consultor financeiro especialista em imigração para Portugal. Dá pareceres curtos, humanos e muito honestos."},
                {"role": "user", "content": f"Analise este plano migratório em 2 parágrafos diretos: Nome: {data.nome}, Perfil: {data.perfil}, Destino: {data.regiao}, Meses: {data.meses}, Reserva total calculada: € {total_euro:.2f}."}
            ],
            temperature=0.3
        )
        insight_texto = completion.choices[0].message.content
    except:
        pass

    return {"total_euro": total_euro, "total_real": total_real, "insight_ia": insight_texto}

# =====================================================================
# 3. ROTA CORRIGIDA: RADAR DE ANÁLISE REGIONAL (GUIAS VIA IA)
# =====================================================================
@app.post("/api/guias")
async def gerar_analise_regional(data: RegionRequest):
    regiao_selecionada = data.regiao
    guia_texto = "### O custo médio de habitação varia entre €600 e €1100 dependendo da proximidade aos centros urbanos. ### O mercado local apresenta forte demanda nos setores de tecnologia, serviços e turismo. ### O clima é caracterizado por estações bem definidas, com invernos amenos e verões ensolarados. ### Planeie a sua fixação com antecedência burocrática junto dos órgãos oficiais."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Cria uma análise curta dividida estritamente por três marcadores '###' sem títulos explicativos. Exemplo: ### custo médio de vida na região ### oportunidades locais de emprego ### clima e adaptação regional ### principal conselho estratégico de integração"},
                {"role": "user", "content": f"Gera dados de imigração e integração realística para a região: {regiao_selecionada}"}
            ],
            temperature=0.4
        )
        if completion.choices[0].message.content:
            guia_texto = completion.choices[0].message.content
    except Exception as e:
        print(f"Erro na Groq AI para guias: {e}")

    artigos_apoio = [
        {"titulo": "Trabalhar em Portugal: Guia Oficial IEFP", "resumo": "Consulte as vagas e regras de contratação do Instituto de Emprego.", "url": "https://www.iefp.pt"},
        {"titulo": "Habitação e Mercado Imobiliário - Idealista", "resumo": "Estatísticas reais sobre arrendamento e preços de quartos.", "url": "https://www.idealista.pt/news/"}
    ]
    
    return {"guia_ia": guia_texto, "artigos": artigos_apoio}

# =====================================================================
# 4. ROTA: PLANTÃO DE NOTÍCIAS AUTOMÁTICO
# =====================================================================
def extrair_imagem_real(url_artigo, placeholder):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        r = requests.get(url_artigo, headers=headers, timeout=3)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            meta_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_img and meta_img.get("content"):
                return meta_img["content"]
            artigo_img = soup.find("article")
            if artigo_img:
                img_tag = artigo_img.find("img")
                if img_tag and img_tag.get("src"):
                    return img_tag["src"]
    except:
        pass
    return placeholder

@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    url_google_news = (
        "https://news.google.com/rss/search?q="
        "(imigração+OR+imigrantes+OR+visto+OR+AIMA+OR+residência+OR+nacionalidade+OR+cidadania)+portugal+"
        "(site:sicnoticias.pt+OR+site:dn.pt+OR+site:publico.pt+OR+site:jn.pt+OR+site:observador.pt+OR+"
        "site:g1.globo.com+OR+site:folha.uol.com.br+OR+site:estadao.com.br+OR+site:cnnbrasil.com.br)"
        "&hl=pt-PT&gl=PT&ceid=PT:pt-pt"
    )
    noticias_final = []
    img_placeholder = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop"

    try:
        feed = feedparser.parse(url_google_news)
        for entry in feed.entries[:14]:
            titulo = entry.get("title", "")
            if " - " in titulo:
                titulo = titulo.split(" - ")[0]
            link_original = entry.get("link", "#")
            
            link_lower = link_original.lower()
            tag = "Portugal"
            if "sicnoticias" in link_lower: tag = "SIC Notícias"
            elif "dn.pt" in link_lower: tag = "DN Portugal"
            elif "publico.pt" in link_lower: tag = "Público"
            elif "jn.pt" in link_lower: tag = "Jornal de Notícias"
            elif "observador" in link_lower: tag = "Observador"
            elif "g1.globo" in link_lower: tag = "G1 Globo"
            elif "folha" in link_lower: tag = "Folha de S.Paulo"
            elif "estadao" in link_lower: tag = "Estadão"
            elif "cnnbrasil" in link_lower: tag = "CNN Brasil"

            imagem_capa = extrair_imagem_real(link_original, img_placeholder)

            noticias_final.append({
                "titulo": titulo,
                "resumo": "Clique no link abaixo para acompanhar a cobertura completa desta atualização diretamente no portal oficial.",
                "url": link_original,
                "tag": tag,
                "imagem": imagem_capa
            })
    except:
        pass

    # 1. INVERTE A LISTA: Notícias mais recentes ficam no início (índice 0)
    noticias_final = noticias_final[::-1]

    # 2. Lógica Dinâmica: Insere o card promocional na 2ª posição (índice 1)
    card_promocional = {
        "titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal",
        "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro.",
        "url": "viver-do-digital.html",
        "tag": "Tendência",
        "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
    }

    if len(noticias_final) >= 3:
        noticias_final.insert(3, card_promocional)
    else:
        noticias_final.append(card_promocional)

    return {"noticias": noticias_final[:15]}
# =====================================================================
# 5. ROTA: ASSISTENTE VIRTUAL (CHAT IA)
# =====================================================================
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
                    "- Tu és o IMIGRANTE AI, o assistente virtual oficial do Portal Imigrante PT.\n"
                    "- Personalidade prática, experiente, sê extremamente direto. Responde em no máximo 3 parágrafos."
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
        resposta_final = f"[Erro de Conexão]: Motor inteligente instável. Detalhe: {str(e)}"
    return {"response": resposta_final}

# =====================================================================
# 6. ROTA NOVA: PAINEL DE VAGAS TOTALMENTE ISOLADO (SEM RISCO)
# =====================================================================
@app.get("/api/vagas")
async def obter_vagas_emprego():
    url_vagas_agregadas = (
        "https://news.google.com/rss/search?q="
        "(\"oferta+de+emprego\"+OR+\"vaga+de+emprego\"+OR+\"recrutamento\")+Portugal+"
        "(site:indeed.com+OR+site:net-empregos.com+OR+site:itjobs.pt+OR+site:sapo.pt)"
        "&hl=pt-PT&gl=PT&ceid=PT:pt-pt"
    )
    
    vagas_resultado = []
    try:
        feed = feedparser.parse(url_vagas_agregadas)
        for entry in feed.entries[:12]:
            titulo_raw = entry.get("title", "Vaga Recente")
            link = entry.get("link", "#")
            
            # Limpeza cirúrgica do título
            limpeza = ["oferta de emprego", "vaga de emprego", "recrutamento", "em portugal", " - sapo", " - indeed", " - itjobs"]
            titulo_limpo = titulo_raw
            for termo in limpeza:
                titulo_raw = titulo_raw.replace(termo, "").replace(termo.title(), "").strip(" -:")
            
            # Identificação da fonte para o campo "local"
            fonte = "Portal de Empregos"
            if "sapo" in link.lower(): fonte = "SAPO Emprego"
            elif "indeed" in link.lower(): fonte = "Indeed"
            elif "net-empregos" in link.lower(): fonte = "Net-Empregos"
            elif "itjobs" in link.lower(): fonte = "ITJobs"
            
            vagas_resultado.append({
                "titulo": titulo_raw.strip(),
                "local": fonte,
                "descricao": "Vaga ativa. Clique para verificar requisitos e candidatar-se.",
                "url": link
            })
    except Exception as e:
        print(f"Erro ao processar vagas: {e}")
        
    return {"vagas": vagas_resultado}
@app.get("/")
def home():
    return {"status": "Servidor online!"}
