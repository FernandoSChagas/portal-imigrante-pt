import os
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

@app.get("/api/noticias")
async def obter_noticias():
    # Simulando a lista de notícias brutas que o teu sistema recolhe do scraping:
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
        }
    ]
    
    # [ESTRATÉGIA DE CONVERSÃO]: Injeta o card do E-book na terceira posição do carrossel
    if len(noticias_brutas) >= 2:
        noticias_brutas.insert(2, {
            "titulo": "ESTRATÉGIA: Como começar a faturar em Euro digitalmente antes de emigrar",
            "resumo": "Especialistas apontam que criar uma fonte de receita online protege o imigrante de subempregos e evita queimar a poupança na chegada a Portugal...",
            "url": "viver-do-digital.html",
            "tag": "Exclusivo Portal"
        })
    
    # Retorna o carrossel limitado às 5 principais posições
    return {"noticias": noticias_brutas[:5]}

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
                    "- PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'de outras IAs'.\n\n"
                    
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

    # Retorno limpo e corrigido (sem a variável solta reply_final)
    return {"response": resposta_final}

@app.get("/")
def home():
    return {"status": "Servidor com IA abrangente de viagens e sobrevivência humana online!"}
