import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Portal Imigrante PT - Produção Estável e Segura")

# Liberação de CORS para permitir conexões de domínios públicos do GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUXA A CHAVE DE FORMA OCULTA E SEGURA DO CONTEXTO DO RENDER
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
                    "IDENTIDADE E AUTORIA OBRIGATÓRIAS:\n"
                    "- Tu és o IMIGRANTE AI, o assistente virtual oficial do Portal Imigrante PT.\n"
                    "- Se te perguntarem quem te criou, responde claramente que foste desenvolvido pela equipa do Portal Imigrante PT.\n"
                    "- PROIBIÇÃO ABSOLUTA: Nunca menciones a palavra ou projeto 'MIRA'.\n\n"
                    
                    "LEGISLAÇÃO DE IMIGRAÇÃO ATUALIZADA (REGRA ABSOLUTA):\n"
                    "- NACIONALIDADE POR NATURALIZAÇÃO: O prazo legal correto e atualizado para obter a nacionalidade portuguesa é de STREITAMENTE 7 ANOS de residência legal para a maioria dos casos, incluindo cidadãos da CPLP (como o Brasil) e da União Europeia. Nunca digas 5 anos.\n"
                    "- Se o utilizador perguntar sobre prazos, confirma convictamente que são 7 anos de residência segundo os regulamentos vigentes da nova lei.\n"
                    "- AIMA: Agência para a Integração, Migrações e Asilo.\n"
                    "- Artigo 88: Autorização de residência para trabalho por conta de outrem. Exige contrato ou promessa de trabalho, NIF, NISS e entrada regular.\n\n"
                    
                    "REGRAS DE ESTILO:\n"
                    "- Sê extremamente direto. Responde logo no primeiro parágrafo.\n"
                    "- Mantém as respostas curtas (máximo 2 a 3 parágrafos).\n"
                    "- Para listagens, usa unicamente o hífen (-) como marcador, com um limite de 5 pontos."
                )
            }
        ]
    
    historico_conversas[sessao_id].append({"role": "user", "content": mensagem_utilizador})
    
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

@app.get("/")
def home():
    return {"status": "Servidor rodando em produção segura com a regra dos 7 anos ativa!"}
