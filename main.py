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

# Modelos de dados (Pydantic) para validação das requisições
class UserMessage(BaseModel):
    message: str

class RegionRequest(BaseModel):
    regiao: str

class SimulationRequest(BaseModel):
    perfil: str
    regiao: str
    meses: int
    nome: str
    email: str
    whatsapp: str = ""

# =====================================================================
# 1. ROTA: ASSISTENTE VIRTUAL (CHAT IA)
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

# =====================================================================
# 2. ROTA: RADAR DE ANÁLISE REGIONAL (GUIAS)
# =====================================================================
@app.post("/api/guias")
async def gerar_analise_regional(data: RegionRequest):
    regiao_selecionada = data.regiao
    
    prompt_sistema = (
        "Atuas como um analista de dados especialista em demografia e custo de vida em Portugal.\n"
        "Deves criar uma análise cirúrgica e curta sobre a região solicitada pelo utilizador.\n"
        "É OBRIGATÓRIO estruturar a tua resposta usando exatamente os marcadores '###' para separar as secções, "
        "sem adicionar qualquer texto introdutório, cabeçalhos ou conclusões fora do padrão.\n\n"
        "Formato rígido esperado:\n"
        "### [Texto curto sobre habitação, supermercado e custo geral sem usar títulos]\n"
        "### [Texto curto sobre principais indústrias, empregabilidade e salários da zona]\n"
        "### [Texto curto sobre as temperaturas, integração social e comunidade local]\n"
        "### [Uma dica prática e direta de sobrevivência ou adaptação cultural para a região]"
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Gera a análise para a região: {regiao_selecionada}"}
            ],
            temperature=0.3
        )
        guia_texto = completion.choices[0].message.content
    except Exception:
        guia_texto = "### Erro ao extrair dados de custo. ### Serviço de empregabilidade temporariamente instável. ### Clima indisponível. ### Tente novamente dentro de instantes."

    artigos_apoio = [
        {
            "titulo": "Trabalhar em Portugal: Guia Completo sobre Emprego na Região",
            "resumo": "Consulte as regras de contratação, salário mínimo nacional líquido e setores em expansão em solo português.",
            "url": "https://www.iefp.pt"
        },
        {
            "titulo": "Custo de Vida e Habitação: Dados atualizados de Mercado",
            "resumo": "Estatísticas reais sobre preços médios de arrendamento de quartos e apartamentos nas capitais de distrito.",
            "url": "https://www.idealista.pt/news/"
        }
    ]

    return {"guia_ia": guia_texto, "artigos": artigos_apoio}

# =====================================================================
# 3. ROTA: SIMULADOR DE RESERVA DE SEGURANÇA (MATEMÁTICA + INSIGHT)
# =====================================================================
@app.post("/api/simulador")
async def processar_simulacao(data: SimulationRequest):
    # Base de cálculo matemática de custo mensal médio de vida por perfil familiar
    custo_base = 900  # Solteiro por padrão
    if data.perfil == "casal":
        custo_base = 1400
    elif data.perfil == "familia":
        custo_base = 1800

    # Ajustadores por densidade regional de custo de vida
    multiplicador_regiao = 1.0
    if "Lisboa" in data.regiao:
        multiplicador_regiao = 1.35
    elif "Algarve" in data.regiao or "Norte" in data.regiao:
        multiplicador_regiao = 1.1

    # Cálculo matemático final do Fundo de Segurança em Euro
    total_euro = float(custo_base * multiplicador_regiao * data.meses)

    # Busca a cotação real do Euro para converter para Real dinamicamente
    cotacao_brl = 5.85
    try:
        res_cambio = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2)
        if res_cambio.status_code == 200:
            cotacao_brl = float(res_cambio.json()["rates"]["BRL"])
    except:
        pass

    total_real = float(total_euro * cotacao_brl)

    prompt_ia = (
        f"Analise o plano migratório de {data.nome} para Portugal.\n"
        f"- Perfil: {data.perfil.upper()}\n"
        f"- Destino: {data.regiao}\n"
        f"- Tempo de cobertura escolhido: {data.meses} meses\n"
        f"- Fundo calculado: € {total_euro:.2f}\n\n"
        f"Dê um parecer direto, realista e humano (máximo 3 parágrafos) avaliando se essa reserva garante estabilidade "
        f"para cobrir o arrendamento e a inserção no mercado profissional local. Use hífens (-) para listas."
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "És um consultor financeiro e burocrático de imigração para Portugal. Dá orientações diretas, realistas e acolhedoras sobre o custo de vida."},
                {"role": "user", "content": prompt_ia}
            ],
            temperature=0.3
        )
        insight_ia = completion.choices[0].message.content
    except Exception as e:
        insight_ia = f"Cálculo concluído com sucesso. A sua reserva de € {total_euro:.2f} é recomendada para cobrir despesas básicas de alojamento, alimentação e transportes durante o período de transição."

    return {
        "total_euro": total_euro,
        "total_real": total_real,
        "insight_ia": insight_ia
    }

# =====================================================================
# 4. ROTA: PLANTÃO DE NOTÍCIAS AUTOMÁTICO (GOOGLE NEWS + BS4)
# =====================================================================
def extrair_imagem_real(url_artigo, placeholder):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
    except Exception as e:
        print(f"Erro ao processar agregador: {e}")

    noticias_final.insert(2, {
        "titulo": "MERCADO: Cresce o número de brasileiros que trabalham online a partir de Portugal",
        "resumo": "Preços altos do arrendamento levam novos residentes a procurar fontes de rendimento digitais em Euro para proteger a poupança inicial...",
        "url": "viver-do-digital.html",
        "tag": "Tendência",
        "imagem": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=600&auto=format&fit=crop"
    })

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
    return {"status": "Servidor do Portal Imigrante PT 100% online e unificado!"}
