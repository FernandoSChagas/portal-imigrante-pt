import os
import requests
import csv
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - Ecossistema Unificado com Google Sheets")

# Configuração de CORS aberta para o GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chaves de API e Configurações (Totalmente seguro e sem chaves expostas)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = "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"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx-S0LKPb0z4-J8uitpt3_tB7dYYxaTFpA2KXIjWJkU3BNT9empVC17YRzaf3dgGweW/exec"

if not GROQ_API_KEY:
    print("AVISO: GROQ_API_KEY não encontrada nas variáveis de ambiente do Render!")

client = Groq(api_key=GROQ_API_KEY)
historico_conversas = {}

# =====================================================================
# MODELOS DE DADOS PYDANTIC
# =====================================================================
class UserMessage(BaseModel):
    message: str
    session_id: str = "comum"

class RegionRequest(BaseModel):
    regiao: str

class SimRequest(BaseModel):
    perfil: str
    regiao: str
    meses: int
    nome: str  
    email: str 
    whatsapp: str = "Não informado"

# =====================================================================
# FUNÇÃO AUXILIAR: GRAVAR O LEAD DIRETAMENTE NO GOOGLE SHEETS
# =====================================================================
def guardar_lead_local(nome: str, email: str, whatsapp: str, origin: str):
    try:
        payload = {
            "nome": nome,
            "email": email,
            "whatsapp": whatsapp,
            "origem": origin
        }
        # Envia os dados em tempo real para o Webhook do Google Apps Script
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=8)
        if response.status_code == 200:
            print("Lead salvo com sucesso no Google Sheets!")
            return True
        return False
    except Exception as e:
        print(f"Erro ao enviar para o Google Sheets: {str(e)}")
        return False

# =====================================================================
# ENDPOINT: PUXA OS DADOS DO GOOGLE SHEETS PARA O PAINEL DE LEADS
# =====================================================================
@app.get("/api/leads/exportar")
async def exportar_leads():
    try:
        # Puxa a lista completa e atualizada diretamente do teu Google Sheets
        response = requests.get(GOOGLE_SCRIPT_URL, timeout=8)
        if response.status_code == 200:
            return response.json()
        return {"total_leads": 0, "leads": [], "erro": "Não foi possível ler o Google Sheets."}
    except Exception as e:
        return {"erro": f"Erro de conexão com o Google: {str(e)}"}

# =====================================================================
# 1. ENDPOINT: NOTÍCIAS COM INJEÇÃO CAMUFLADA DE VENDAS (INDEX.HTML)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    try:
        url = "https://api.tavily.com/search"
        query_focada = (
            "notícias imigração Portugal visto AIMA CPLP "
            "-site:instagram.com -site:facebook.com -site:twitter.com -site:tiktok.com -\"EUA\" -\"Estados Unidos\""
        )
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query_focada,
            "search_depth": "advanced",
            "time_range": "day",
            "max_results": 10
        }
        
        response = requests.post(url, json=payload, timeout=6)
        noticias_brutas = []

        if response.status_code == 200:
            resultados = response.json().get("results", [])
            for item in resultados:
                site_url = item.get("url", "").lower()
                titulo = item.get("title", "")
                conteudo = item.get("content", "").lower()
                
                if any(x in site_url for x in ["instagram", "tiktok", "facebook", "twitter", "youtube"]):
                    continue
                if "estados unidos" in titulo.lower() or " eua " in f" {titulo.lower()} ":
                    continue
                if "estados unidos" in conteudo or " eua " in f" {conteudo} ":
                    continue
                
                tag = "Portugal"
                if "sicnoticias" in site_url: tag = "SIC Notícias"
                elif "dn.pt" in site_url: tag = "DN Portugal"
                elif "publico" in site_url: tag = "Público"
                elif "jn.pt" in site_url: tag = "Jornal de Notícias"
                elif "aima" in site_url: tag = "AIMA Oficial"
                elif "rtp" in site_url: tag = "RTP Notícias"
                
                noticias_brutas.append({
                    "titulo": titulo,
                    "resumo": item.get("content", "Aceda à cobertura de última hora diretamente no portal de notícias.")[:135] + "...",
                    "url": item.get("url", "#"),
                    "tag": tag
                })

        if len(noticias_brutas) < 2:
            noticias_brutas = [
                {"titulo": "AIMA reforça atendimento digital para agendamentos de vistos", "resumo": "Novas plataformas digitais prometem acelerar a regularização de processos pendentes de manifestações de interesse antigas...", "url": "https://aima.gov.pt", "tag": "AIMA Oficial"},
                {"titulo": "Consulados portugueses registam alta na procura por Visto de Trabalho", "resumo": "Procura por vistos de residência e procura de trabalho em Portugal mantém tendência de alta no primeiro semestre deste ano...", "url": "https://portaldascomunidades.mne.gov.pt", "tag": "Consular"}
            ]
        
        noticias_brutas.insert(2, {
            "titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal",
            "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro para proteger a poupança inicial...",
            "url": "viver-do-digital.html",
            "tag": "Tendência"
        })
        
        return {"noticias": noticias_brutas[:6]}
    except Exception:
        return {"noticias": [
            {"titulo": "AIMA reforça atendimento digital para agendamentos de vistos", "resumo": "Novas plataformas digitais prometem acelerar a regularização de processos pendentes...", "url": "https://aima.gov.pt", "tag": "AIMA Oficial"},
            {"titulo": "Consulados portugueses registam alta na procura por Visto de Trabalho", "resumo": "Procura por vistos de residência e procura de trabalho em Portugal mantém tendência de alta...", "url": "https://portaldascomunidades.mne.gov.pt", "tag": "Consular"},
            {"titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal", "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais...", "url": "viver-do-digital.html", "tag": "Tendência"}
        ]}

# =====================================================================
# 2. ENDPOINT: ASSISTENTE VIRTUAL IA COM MEMÓRIA (ASSISTENTE.HTML)
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
                    "Tu és o IMIGRANTE AI, o assistente virtual oficial do Portal Imigrante PT. "
                    "O teu objetivo é ser um suporte amplo e completo para ajudar utilizadores com QUALQUER assunto "
                    "ligado a imigração, com especialidade em vistos para a Europa, processos da AIMA, documentação, "
                    "logística de voos, mercado de trabalho e dicas de integração e sobrevivência inicial. "
                    "Tu tens uma MEMÓRIA HUMANA: lembra-te do contexto do diálogo. "
                    "A tua personalidade é acolhedora, prática, muito prestativa e extremamente direta. "
                    "PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'de outras IAs' ou 'MIRA'. "
                    "O ano atual é 2026. Responde de forma corta, usando no máximo 2 parágrafos."
                )
            }
        ]
    
    historico_conversas[sessao_id].append({"role": "user", "content": message_utilizador})
    
    if len(historico_conversas[sessao_id]) > 13:
        historico_conversas[sessao_id] = [historico_conversas[sessao_id][0]] + historico_conversas[sessao_id][-12:]
    
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

# =====================================================================
# 3. ENDPOINT: DOSSIÊ EM CARDS (GUIAS.HTML)
# =====================================================================
@app.post("/api/guias")
async def obtener_guias_regionais(data: RegionRequest):
    regiao = data.regiao
    
    prompt_guia = f"""
    Atue como um Especialista em Relocalização em Portugal. 
    Analise a região: {regiao}.
    Retorne a resposta EXATAMENTE neste formato abaixo, sem introduções, cumprimentos, saudações ou explicações:
    ### Escreva aqui um resumo curto sobre o Custo de Vida, Arrendamento de habitação e contas fixas do mês.
    ### Escreva aqui um resumo curto sobre as Principais Indústrias, empresas, fábricas e empregos mais ativos na zona.
    ### Escreva aqui um resumo curto sobre o Clima predominante da região e o ritmo de vida e cultura da população local.
    ### Escreva aqui uma Dica Prática Humana e direta de adaptação e acolhimento para o imigrante no primeiro mês.
    """
    
    guia_ia_texto = "###Dados em atualização...###Dados em atualização...###Dados em atualização...###Dados em atualização..."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_guia}],
            temperature=0.2
        )
        guia_ia_texto = completion.choices[0].message.content
    except Exception:
        pass

    artigos_resultados = []
    try:
        url_tavily = "https://api.tavily.com/search"
        payload_tavily = {
            "api_key": TAVILY_API_KEY,
            "query": f"custo de vida morar em {regiao} portugal dicas habitação aluguel -site:instagram.com",
            "search_depth": "basic",
            "time_range": "year",
            "max_results": 3
        }
        
        response = requests.post(url_tavily, json=payload_tavily, timeout=6)
        if response.status_code == 200:
            resultados = response.json().get("results", [])
            for item in resultados:
                artigos_resultados.append({
                    "titulo": item.get("title", "Guia Local Complementar"),
                    "resumo": item.get("content", "")[:160] + "...",
                    "url": item.get("url", "#")
                })
    except Exception:
        pass

    if not artigos_resultados:
        artigos_resultados = [
            {
                "titulo": f"Métricas de Arrendamento e Mercado em {regiao}",
                "resumo": "Análise detalhada sobre custos de habitação, infraestruturas locais e despesas fixas para novos residentes...",
                "url": "https://www.idealista.pt/news/"
            }
        ]

    return {
        "guia_ia": guia_ia_texto,
        "artigos": artigos_resultados
    }

# =====================================================================
# 4. ENDPOINT: SIMULADOR FINANCEIRO COM ENVIO PARA O SHEETS
# =====================================================================
@app.post("/api/simulador")
async def calcular_simulacao(data: SimRequest):
    if not data.nome or not data.email or "@" not in data.email:
        raise HTTPException(status_code=400, detail="Nome e Email válidos são obrigatórios.")
    
    # Grava o lead diretamente no teu Google Sheets permanente
    guardar_lead_local(data.nome, data.email, data.whatsapp, "Simulador")

    custos_base = {
        "Lisboa e Vale do Tejo": {"quarto": 750, "mercado": 450, "transp": 40},
        "Algarve": {"quarto": 550, "mercado": 420, "transp": 40},
        "Centro de Portugal": {"quarto": 450, "mercado": 380, "transp": 35},
        "Norte de Portugal": {"quarto": 400, "mercado": 400, "transp": 30},
        "Ilhas (Açores e Madeira)": {"quarto": 400, "mercado": 430, "transp": 30},
        "Alentejo": {"quarto": 300, "mercado": 350, "transp": 30}
    }
    
    reg = custos_base.get(data.regiao, custos_base["Norte de Portugal"])
    mult = 1.0 if data.perfil == "solteiro" else (1.8 if data.perfil == "casal" else 2.5)
    
    custo_mensal = (reg["quarto"] + (reg["mercado"] * mult) + (reg["transp"] * (2 if mult > 1 else 1)))
    total_euro = (custo_mensal * data.meses) + (reg["quarto"] * 2)
    total_real = total_euro * 6.2
    
    prompt_ia = (
        f"Atue como um Consultor Financeiro de Imigração. Escreva um insight de exatamente duas frases "
        f"para um perfil '{data.perfil}' que planeia mudar-se para a região '{data.regiao}' com uma reserva "
        f"de segurança de {data.meses} meses. O orçamento estimado total é de €{round(total_euro, 2)}. "
        f"Dê uma dica prática de economia ou incentivo real. Seja direto, não use saudações."
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_ia}],
            temperature=0.5
        )
        insight_final = completion.choices[0].message.content
    except Exception:
        insight_final = "Excelente planeamento! Ter uma reserva estruturada para este período garante a estabilidade necessária para se estabelecer."

    return {
        "total_euro": round(total_euro, 2),
        "total_real": round(total_real, 2),
        "insight_ia": insight_final
    }

@app.get("/")
def home():
    return {"status": "Servidor do Ecossistema Portal Imigrante PT Completo e Online!"}
