import os
import requests
import csv
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - Ecossistema Unificado com Leads")

# Configuração de CORS aberta para o GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chaves de API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
TAVILY_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
historico_conversas = {}

# Ficheiro onde os leads serão guardados no servidor
LEADS_FILE = "leads_portal.csv"

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
    # Campos opcionais caso queiras capturar o lead direto no clique do simulador
    nome: str = None
    email: str = None
    whatsapp: str = None

class LeadRequest(BaseModel):
    nome: str
    email: str
    whatsapp: str
    origem: str = "geral"

# =====================================================================
# FUNÇÃO AUXILIAR: GUARDAR LEAD NO FICHEIRO CSV
# =====================================================================
def guardar_lead_local(nome: str, email: str, whatsapp: str, origem: str):
    try:
        ficheiro_existe = os.path.exists(LEADS_FILE)
        with open(LEADS_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not ficheiro_existe:
                # Cabeçalho do CSV
                writer.writerow(["Data/Hora", "Nome", "Email", "WhatsApp", "Origem"])
            
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([data_atual, nome, email, whatsapp, origem])
        return True
    except Exception as e:
        print(f"Erro ao guardar lead: {str(e)}")
        return False

# =====================================================================
# NOVO ENDPOINT: CAPTURA DE LEADS AVULSO (FORMULÁRIOS / POPUPS)
# =====================================================================
@app.post("/api/leads")
async def capturar_lead(data: LeadRequest):
    sucesso = guardar_lead_local(data.nome, data.email, data.whatsapp, data.origem)
    if sucesso:
        return {"status": "sucesso", "mensagem": "Lead capturado com sucesso!"}
    return {"status": "erro", "mensagem": "Não foi possível salvar o lead."}

# EXCLUSIVO: Endpoint secreto para tu descarregares os teus leads em tempo real
@app.get("/api/leads/exportar")
async def exportar_leads():
    if not os.path.exists(LEADS_FILE):
        return {"mensagem": "Nenhum lead capturado ainda."}
    
    leads = []
    with open(LEADS_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.dictReader(f) if hasattr(csv, 'dictReader') else csv.Reader(f)
        # Leitura simples para retorno JSON rápido
        linhas = list(reader)
    return {"leads": linhas}

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
                    "O ano atual é 2026. Responde de forma curta, usando no máximo 2 parágrafos."
                )
            }
        ]
    
    historico_conversas[sessao_id].append({"role": "user", "content": mensagem_utilizador})
    
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
# 4. ENDPOINT: SIMULADOR FINANCEIRO COM CAPTURA (SIMULADOR.HTML)
# =====================================================================
@app.post("/api/simulador")
async def calcular_simulacao(data: SimRequest):
    # Se o formulário do simulador enviar dados do utilizador, guarda automaticamente
    if data.nome and data.email:
        guardar_lead_local(data.nome, data.email, data.whatsapp or "Não informado", "simulador")

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
        f"Dê uma dica prática de economia ou incentive real. Seja direto, não use saudações."
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_ia}],
            temperature=0.5
        )
        insight_final = completion.choices[0].message.content
    except Exception:
        insight_final = "Excelente planeamento! Ter uma reserva estruturada para este período garante a estabilidade necessária para se estabelecer e integrar com sucesso."

    return {
        "total_euro": round(total_euro, 2),
        "total_real": round(total_real, 2),
        "insight_ia": insight_final
    }

@app.get("/")
def home():
    return {"status": "Servidor do Ecossistema Portal Imigrante PT Completo e Online!"}
