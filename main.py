import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - IA Humana e Abrangente")

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)

historico_conversas = {}

class UserMessage(BaseModel):
    message: str

# Modelos de dados para as rotas do Simulador e Relatórios não quebrarem
class SimuladorData(BaseModel):
    salario_bruto: float = 1000.0
    num_dependentes: int = 0

# =====================================================================
# 1. ENDPOINT DE NOTÍCIAS (GARANTINDO FLUXO DE MAIS NOTÍCIAS)
# =====================================================================
@app.get("/api/noticias")
async def obter_noticias():
    # Base sólida de notícias para o teu carrossel nunca ficar vazio
    noticias_brutas = [
        {
            "titulo": "AIMA acelera processos de regularização com novos balcões de atendimento",
            "resumo": "Novas medidas descentralizadas prometem reduzir o tempo de espera para manifestações de interesse e agendamentos estruturais em Portugal.",
            "url": "noticia-aima-balcoes.html",
            "tag": "Nacional"
        },
        {
            "titulo": "Mercado de arrendamento no Porto e Braga regista ligeira estabilização de preços",
            "resumo": "Estudos recentes apontam para um aumento na oferta de quartos e apartamentos T1 nas zonas periféricas de Braga e Guimarães.",
            "url": "noticia-arrendamento-norte.html",
            "tag": "Habitação"
        },
        {
            "titulo": "Custo de vida em Portugal 2026: Principais aumentos e como se proteger",
            "resumo": "Relatório detalha o impacto da inflação nos supermercados e nos passes de transporte público nas áreas metropolitanas.",
            "url": "noticia-custo-vida.html",
            "tag": "Economia"
        },
        {
            "titulo": "SNS cria linha de atendimento prioritária para residentes estrangeiros",
            "resumo": "O objetivo é facilitar o registo nos centros de saúde locais e acelerar a atribuição do número de utente para novos imigrantes.",
            "url": "noticia-sns-utente.html",
            "tag": "Saúde"
        }
    ]
    
    # Injeta a tua estratégia de vendas exatamente na 3ª posição (Índice 2)
    noticias_brutas.insert(2, {
        "titulo": "ESTRATÉGIA: Como começar a faturar em Euro digitalmente antes de emigrar",
        "resumo": "Especialistas apontam que criar uma fonte de receita online protege o imigrante de subempregos e evita queimar a poupança na chegada a Portugal...",
        "url": "viver-do-digital.html",
        "tag": "Exclusivo Portal"
    })
    
    return {"noticias": noticias_brutas}

# =====================================================================
# 2. ENDPOINT DO SIMULADOR FINANCEIRO (REATIVADO)
# =====================================================================
@app.post("/api/simulador")
async def calcular_simulacao(data: SimuladorData):
    # Lógica de cálculo padrão para evitar o erro de tela do simulador
    desconto_seg_social = data.salario_bruto * 0.11
    # Simulação simples de retenção de IRS
    taxa_irs = 0.09 if data.salario_bruto <= 1000 else 0.15
    desconto_irs = data.salario_bruto * taxa_irs
    salario_liquido = data.salario_bruto - desconto_seg_social - desconto_irs
    
    return {
        "status": "sucesso",
        "salario_bruto": data.salario_bruto,
        "seguranca_social": round(desconto_seg_social, 2),
        "irs": round(desconto_irs, 2),
        "salario_liquido": round(salario_liquido, 2)
    }

# =====================================================================
# 3. ENDPOINT DE RELATÓRIOS / GUIAS REGIONAIS (REATIVADO)
# =====================================================================
@app.post("/api/relatorios")
@app.get("/api/relatorios")
async def gerar_relatorio_guia(regiao: str = "Norte"):
    return {
        "status": "sucesso",
        "regiao": regiao,
        "mensagem": f"Relatório regional de {regiao} gerado com sucesso.",
        "dados": {
            "custo_medio_quarto": "300€ a 450€",
            "empregabilidade": "Alta (Setores de Serviços, Tecnologia e Indústria)",
            "transportes": "Excelente cobertura regional de comboios e autocarros"
        }
    }

# =====================================================================
# 4. ENDPOINT DO ASSISTENTE CHAT IA
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
                    "- A tua personalidade é acolhedora, prática, experiente e muito realista.\n"
                    "- PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'de outras IAs'.\n\n"
                    "ESCOPO DE ATUAÇÃO:\n"
                    "1. LOGÍSTICA DE VIAGEM E VOOS.\n"
                    "2. DICAS HUMANAS E REAIS DE SOBREVIVÊNCIA.\n"
                    "3. BUROCRACIA LEGAL: Regra dos 7 anos (Lei de 2026), NIF, NISS e AIMA.\n\n"
                    "TONALIDADE:\n"
                    "- Responde de forma curta, direta e fácil de ler no telemóvel (máximo 3 parágrafos)."
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
    return {"status": "Servidor com IA e Motores de Cálculo Online!"}
