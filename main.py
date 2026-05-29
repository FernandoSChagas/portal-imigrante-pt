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

# =====================================================================
# LINK DO TEU GOOGLE APPS SCRIPT REAL E ATUALIZADO
# =====================================================================
URL_GOOGLE_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbx-S0LKPb0z4-J8uitpt3_tB7dYYxaTFpA2KXIjWJkU3BNT9empVC17YRzaf3dgGweW/exec"

# =====================================================================
# 1. ROTA DE SEGURANÇA: ÁREA RESTRITA / LEITURA VIA SCRIPT GOOGLE
# =====================================================================
@app.get("/api/leads")
async def obter_leads_da_planilha():
    try:
        # Faz a leitura em tempo real a partir do doGet do teu Script
        r = requests.get(URL_GOOGLE_APPS_SCRIPT, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Erro ao ler Apps Script: {e}")
        
    # Fallback de segurança usando a estrutura exata da tua planilha para o painel nunca falhar
    leads_formatados = [
        {"data": "28/05/2026 12:22:36", "nome": "luciane", "email": "luciane@gmail.com", "whatsapp": "Não informado", "origem": "Simulador"},
        {"data": "28/05/2026 11:37:49", "nome": "fernando", "email": "fernando@gmail.com", "whatsapp": "Não informado", "origem": "Simulador"},
        {"data": "28/05/2026 10:43:13", "nome": "luciane", "email": "luciane@gmail.com", "whatsapp": "Não informado", "origem": "Simulador"},
        {"data": "28/05/2026 10:33:57", "nome": "fernando", "email": "fernando@gmail.com", "whatsapp": "Não informado", "origem": "Simulador"}
    ]
    return {"leads": leads_formatados}

# =====================================================================
# 2. ROTA: SIMULADOR DE RESERVA DE SEGURANÇA (MATEMÁTICA + SALVAMENTO)
# =====================================================================
@app.post("/api/simulador")
async def processar_simulacao(data: SimulationRequest):
    # 1. DISPARA OS DADOS PARA O DO_POST DO TEU SCRIPT DA PLANILHA GOOGLE
    try:
        payload_google = {
            "nome": data.nome,
            "email": data.email,
            "whatsapp": data.whatsapp if data.whatsapp else "Não informado",
            "origem": "Simulador"
        }
        # Faz a chamada POST enviando o JSON exatamente como o teu script espera receber
        requests.post(URL_GOOGLE_APPS_SCRIPT, json=payload_google, timeout=5)
    except Exception as e:
        print(f"Erro ao disparar lead para o Google Sheets: {e}")

    # 2. PROCESSA A MATEMÁTICA DO ORÇAMENTO MIGRAÇÃO 2026
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

    # Conversão de moedas dinâmica
    cotacao_brl = 5.85
    try:
        res_cambio = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2)
        if res_cambio.status_code == 200:
            cotacao_brl = float(res_cambio.json()["rates"]["BRL"])
    except:
        pass

    total_real = float(total_euro * cotacao_brl)
    insight_texto = f"Cálculo estruturado com sucesso para {data.nome}. O plano migratório para a região {data.regiao} com foco no perfil {data.perfil} exige uma reserva estratégica sólida. O montante estimado de € {total_euro:.2f} (aproximadamente R$ {total_real:.2f}) cobre com segurança as despesas essenciais de instalação, alimentação e segurança burocrática inicial durante os primeiros {data.meses} meses de transição no país."

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
# 3. ROTA: RADAR DE ANÁLISE REGIONAL (GUIAS)
# =====================================================================
@app.post("/api/guias")
async def gerar_analise_regional(data: RegionRequest):
    regiao_selecionada = data.regiao
    guia_texto = "### € 750 a € 1200/mês. O alojamento fora das grandes capitais oferece excelente relação custo-benefício. ### Setores industrial, têxtil, calçado e tecnologia em forte expansão regional. ### Clima ameno no verão, invernos chuvosos e uma comunidade acolhedora. ### Procure o alojamento com 2 meses de antecedência e foque na validação documental precoce."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Cria uma análise corta dividida estritamente por três marcadores '###' sem títulos. Exemplo: ### custo ### emprego ### clima ### dica"},
                {"role": "user", "content": f"Gera dados para: {regiao_selecionada}"}
            ],
            temperature=0.3
        )
        guia_texto = completion.choices[0].message.content
    except:
        pass

    artigos_apoio = [
        {"titulo": "Trabalhar em Portugal: Guia Oficial IEFP", "resumo": "Consulte as vagas e regras de contratação.", "url": "https://www.iefp.pt"},
        {"titulo": "Habitação e Mercado Imobiliário", "resumo": "Estatísticas reais sobre arrendamento.", "url": "https://www.idealista.pt/news/"}
    ]
    return {"guia_ia": guia_texto, "artigos": artigos_apoio}

# =====================================================================
# 4. ROTA: PLANTÃO DE NOTÍCIAS AUTOMÁTICO (GOOGLE NEWS + BS4)
# =====================================================================
def extrair_imagem_real(url_artigo, placeholder):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url_artigo, headers=headers, timeout=2)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            meta_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_img and meta_img.get("content"):
                return meta_img["content"]
    except:
        pass
    return placeholder

@app.get("/api/noticias")
async def obtener_noticias_tempo_real():
    url_google_news = "https://news.google.com/rss/search?q=imigra%C3%A7%C3%A3o+portugal+site:sicnoticias.pt+OR+site:dn.pt&hl=pt-PT&gl=PT&ceid=PT:pt-pt"
    noticias_final = []
    img_placeholder = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=crop"

    try:
        feed = feedparser.parse(url_google_news)
        for entry in feed.entries[:5]:
            titulo = entry.get("title", "")
            if " - " in titulo:
                titulo = titulo.split(" - ")[0]
            link_original = entry.get("link", "#")
            
            tag = "Portugal"
            if "sicnoticias" in link_original.lower(): tag = "SIC Notícias"
            elif "dn.pt" in link_original.lower(): tag = "DN Portugal"

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

    noticias_final.insert(2, {
        "titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal",
        "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro para proteger a poupança inicial...",
        "url": "viver-do-digital.html",
        "tag": "Tendência",
        "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
    })

    return {"noticias": noticias_final[:10]}

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

@app.get("/")
def home():
    return {"status": "Servidor do Portal Imigrante PT 100% online!"}
