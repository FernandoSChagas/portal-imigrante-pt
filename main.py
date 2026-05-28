import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - Notícias Estáveis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = "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"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx-S0LKPb0z4-J8uitpt3_tB7dYYxaTFpA2KXIjWJkU3BNT9empVC17YRzaf3dgGweW/exec"

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
historico_conversas = {}

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

def guardar_lead_local(nome: str, email: str, whatsapp: str, origin: str):
    try:
        payload = {"nome": nome, "email": email, "whatsapp": whatsapp, "origem": origin}
        requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=8)
        return True
    except Exception:
        return False

@app.get("/api/leads/exportar")
async def exportar_leads():
    try:
        response = requests.get(GOOGLE_SCRIPT_URL, timeout=8)
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

# =====================================================================
# ROTA DE NOTÍCIAS COMPLETA (NOTÍCIAS REAIS DE PORTUGAL)
# =====================================================================
@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    # Criamos a lista padrão fora do bloco try para ser usada em qualquer falha
    lista_seguranca = [
        {"titulo": "AIMA lança mutirão digital para atualizar processos", "resumo": "Nova força-tarefa digital pretende agilizar a validação de dados de manifestações de interesse antigas...", "url": "https://aima.gov.pt", "tag": "AIMA Oficial", "imagem": "https://images.unsplash.com/photo-1450133064473-71024230f91b?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "Segurança Social adota novo sistema de agendamento", "resumo": "Medida visa reduzir as filas de espera e facilitar a atribuição do NISS para novos residentes estrangeiros...", "url": "https://www.seg-social.pt", "tag": "Segurança Social", "imagem": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "Custo de arrendamento estabiliza em áreas metropolitanas", "resumo": "Dados do mercado imobiliário do Grande Porto e Centro indicam uma ligeira redução na pressão dos novos contratos...", "url": "https://dn.pt", "tag": "DN Portugal", "imagem": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "Novas regras do Espaço Schengen entram em vigor", "resumo": "Alterações no controlo de fronteiras prometem maior automatização e impacto nos vistos de turismo...", "url": "https://sicnoticias.pt", "tag": "SIC Notícias", "imagem": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "IRN abre novos balcões para emissão de passaportes", "resumo": "Iniciativa pretende descentralizar o atendimento em Lisboa e Porto, reduzindo os prazos médios de entrega...", "url": "https://irn.justica.gov.pt", "tag": "IRN Oficial", "imagem": "https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "CPLP avalia novas facilidades para mobilidade laboral", "resumo": "Países membros discutem em cimeira novos acordos para simplificar a equivalência de diplomas...", "url": "https://www.rtp.pt", "tag": "RTP Notícias", "imagem": "https://images.unsplash.com/photo-1521791136368-1a46827d0505?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "Finanças simplificam emissão de faturas independentes", "resumo": "Autoridade Tributária atualiza portal com guias práticos focados em imigrantes que prestam serviços online...", "url": "https://portaldasfinancas.gov.pt", "tag": "Finanças", "imagem": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "Mercado imobiliário em Braga regista recorde de alojamentos", "resumo": "Aumento da oferta de quartos e apartamentos partilhados traz alívio financeiro para estudantes...", "url": "https://publico.pt", "tag": "Público", "imagem": "https://images.unsplash.com/photo-1513694203232-719a280e022f?q=80&w=600&auto=format&fit=crop"},
        {"titulo": "Politécnicos abrem vagas para estudantes internacionais", "resumo": "Processo de candidatura simplificado atrai recorde de novos alunos da comunidade de língua portuguesa...", "url": "https://dges.gov.pt", "tag": "Educação", "imagem": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?q=80&w=600&auto=format&fit=crop"}
    ]

    try:
        url = "https://api.tavily.com/search"
        query_focada = "notícias imigração Portugal AIMA vistos"
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query_focada,
            "search_depth": "advanced",
            "max_results": 20,
            "include_images": True
        }
        
        response = requests.post(url, json=payload, timeout=8)
        noticias_brutas = []
        img_placeholder = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop"

        if response.status_code == 200:
            data_json = response.json()
            resultados = data_json.get("results", [])
            imagens_tavily = data_json.get("images", [])
            
            for idx, item in enumerate(resultados):
                site_url = item.get("url", "").lower()
                titulo = item.get("title", "")
                
                if any(x in site_url for x in ["instagram", "tiktok", "facebook", "twitter", "youtube"]): 
                    continue
                
                tag = "Portugal"
                if "sicnoticias" in site_url: tag = "SIC Notícias"
                elif "dn.pt" in site_url: tag = "DN Portugal"
                elif "publico.pt" in site_url: tag = "Público"
                elif "jn.pt" in site_url: tag = "Jornal de Notícias"
                elif "aima" in site_url: tag = "AIMA Oficial"
                elif "rtp.pt" in site_url: tag = "RTP Notícias"
                elif "cnnportugal" in site_url: tag = "CNN Portugal"
                
                img_url = imagens_tavily[idx] if idx < len(imagens_tavily) else img_placeholder
                if not img_url or not str(img_url).startswith("http"):
                    img_url = img_placeholder

                noticias_brutas.append({
                    "titulo": titulo,
                    "resumo": item.get("content", "Atualização recente sobre imigração em Portugal.")[:120] + "...",
                    "url": item.get("url", "#"),
                    "tag": tag,
                    "imagem": img_url
                })

        noticias_limpas = []
        vistas = set()
        for n in noticias_brutas:
            if n["titulo"] not in vistas:
                vistas.add(n["titulo"])
                noticias_limpas.append(n)

        # Se a API do Tavily falhar em trazer dados novos, usa a lista padrão estável
        if len(noticias_limpas) < 8:
            noticias_limpas = lista_seguranca

        # INJEÇÃO ESTRATÉGICA DO E-BOOK (Posição 3)
        noticias_limpas.insert(2, {
            "titulo": "MERCADO: Cresce o trabalho online para brasileiros em Portugal",
            "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro...",
            "url": "viver-do-digital.html",
            "tag": "Tendência",
            "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
        })
        
        return {"noticias": noticias_limpas[:9]}
        
    except Exception:
        # Se houver um erro crítico no servidor, garante o envio dos 9 cards estruturados
        lista_seguranca.insert(2, {
            "titulo": "MERCADO: Cresce o trabalho online para brasileiros em Portugal",
            "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro...",
            "url": "viver-do-digital.html",
            "tag": "Tendência",
            "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
        })
        return {"noticias": lista_seguranca[:9]}

@app.post("/api/chat")
async def responder_chat(user_data: UserMessage):
    mensagem_utilizador = user_data.message
    sessao_id = user_data.session_id 
    if sessao_id not in historico_conversas:
        historico_conversas[sessao_id] = [{"role": "system", "content": "Tu és o IMIGRANTE AI, assistente do Portal Imigrante PT. Responde de forma curta e direta em até 2 parágrafos. O ano é 2026."}]
    historico_conversas[sessao_id].append({"role": "user", "content": message_utilizador})
    try:
        completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=historico_conversas[sessao_id], temperature=0.2)
        resposta_final = completion.choices[0].message.content
        historico_conversas[sessao_id].append({"role": "assistant", "content": resposta_final})
    except Exception as e:
        resposta_final = f"[Erro]: {str(e)}"
    return {"response": resposta_final}

@app.post("/api/guias")
async def obtener_guias_regionais(data: RegionRequest):
    regiao = data.regiao
    prompt = f"Especialista em Relocalização. Analise a região: {regiao}. Use formato ### Custo de vida ### Empregos ### Clima ### Dica Prática."
    guia_ia_texto = "###Dados em atualização..."
    try:
        completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=0.2)
        guia_ia_texto = completion.choices[0].message.content
    except Exception: pass
    return {"guia_ia": guia_ia_texto, "artigos": [{"titulo": f"Métricas de Arrendamento em {regiao}", "resumo": "Análise sobre custos de habitação...", "url": "https://www.idealista.pt/news/"}]}

@app.post("/api/simulador")
async def calcular_simulacao(data: SimRequest):
    if not data.nome or not data.email or "@" not in data.email: raise HTTPException(status_code=400, detail="Dados inválidos.")
    guardar_lead_local(data.nome, data.email, data.whatsapp, "Simulador")
    custo_mensal = 850
    total_euro = (custo_mensal * data.meses) + 900
    total_real = total_euro * 6.2
    return {"total_euro": round(total_euro, 2), "total_real": round(total_real, 2), "insight_ia": "Excelente planeamento financeiro para a sua mudança!"}

@app.get("/")
def home():
    return {"status": "Online"}
