import os
import unicodedata
import sqlite3
from json import dumps
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv()

# Inicializa o Servidor Web (Nó de Endpoint de API)
app = Flask(__name__)

# ##############################################################################
# NÓ 1: BANCO DE DADOS DE MEMÓRIA CURTA REAL (SQLite)
# ##############################################################################
DB_PATH = "dados/historico_whatsapp.db"
os.makedirs("dados", exist_ok=True)

def inicializar_banco_de_dados():
    """Cria a tabela de histórico de mensagens se não existir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

def obter_historico_mensagens_sqlite(session_id: str):
    """Busca o histórico de conversas do banco de dados e converte para objetos do LangChain."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM historico WHERE session_id = ? ORDER BY id ASC", (session_id,))
    linhas = cursor.fetchall()
    conn.close()
    
    mensagens = []
    for role, content in linhas:
        if role == "user":
            mensagens.append(HumanMessage(content=content))
        elif role == "assistant":
            # Aqui simplificamos para leitura, tratando como resposta de texto simples da IA
            mensagens.append(AIMessage(content=content))
    return mensagens

def salvar_mensagem_sqlite(session_id: str, role: str, content: str):
    """Grava fisicamente a nova mensagem no banco de dados de memória curta."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO historico (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

inicializar_banco_de_dados()

# ##############################################################################
# NÓ 2: AS FERRAMENTAS DO ROBÔ (Estoque e Calculadora)
# ##############################################################################
def remover_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")

@tool
def buscar_produto_ou_promocao(nome_produto: str) -> str:
    """Busca o preço, estoque ou promoções de um produto na planilha da loja."""
    estoque_simulado = {
        "camisa": "Camisa Polo Oficial - Preço: R$ 89,90 | Estoque: 15 unidades | Promoção: Leve 3 por R$ 240,00",
        "tenis": "Tênis Running Sport - Preço: R$ 199,90 | Estoque: 4 unidades | Sem promoções ativas",
        "bone": "Boné Aba Curva Street - Preço: R$ 45,00 | Estoque: 0 unidades (Esgotado)"
    }
    produto_limpo = remover_acentos(nome_produto.lower().strip())
    for chave in estoque_simulado:
        if chave in produto_limpo or produto_limpo in chave:
            return estoque_simulado[chave]
    return f"Produto '{nome_produto}' não encontrado. Temos disponíveis: camisa, tenis e bone."

@tool
def calcular_orcamento_com_desconto(valor_total: float, cupom: str) -> str:
    """Calcula o valor final de uma compra aplicando cupons de desconto."""
    desconto = 0.0
    if cupom.upper() == "QUERO10":
        desconto = 0.10
    elif cupom.upper() == "VIP20":
        desconto = 0.20
    valor_final = valor_total * (1 - desconto)
    return f"Cálculo Concluído: Valor Original: R$ {valor_total:.2f} | Desconto Aplicado: {desconto*100:.0f}% | Total a Pagar: R$ {valor_final:.2f}"

dicionario_de_ferramentas = {
    "buscar_produto_ou_promocao": buscar_produto_ou_promocao,
    "calcular_orcamento_com_desconto": calcular_orcamento_com_desconto
}

# ##############################################################################
# NÓ 3: INTELIGÊNCIA ARTIFICIAL (Groq Llama 3.1)
# ##############################################################################
modelo_base = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)
modelo_com_ferramentas = modelo_base.bind_tools(list(dicionario_de_ferramentas.values()))

prompt_sistema = """Você é um Atendente Comercial de WhatsApp sênior e automatizado.
Sua missão é responder o cliente com base estritamente nas informações retornadas pelas ferramentas.

REGRAS DE CONTROLE CRÍTICAS (API GROQ):
1. Você está PROIBIDO de chamar múltiplas ferramentas ou fazer chamadas paralelas de uma vez só. 
2. Se o cliente perguntar por mais de um produto, chame a ferramenta para apenas um produto primeiro e de forma sequencial nas rodadas seguintes.
3. Ao final, junte as respostas de todas as ferramentas e responda o cliente em tópicos claros.
"""

# ##############################################################################
# NÓ 4: ENDPOINT DA API DO WHATSAPP (A Interface Online)
# ##############################################################################
@app.route("/webhook", methods=["POST"])
def webhook_whatsapp():
    """Recebe as requisições de mensagens vindas da API do WhatsApp."""
    dados = request.get_json()
    
    # Captura quem enviou (número do telefone do cliente) e a mensagem de texto
    # Essa estrutura simula o padrão de mercado das APIs integradoras
    id_cliente = dados.get("from", "cliente_desconhecido")
    mensagem_cliente = dados.get("message", "")
    
    if not mensagem_cliente:
        return jsonify({"status": "erro", "mensagem": "Mensagem vazia"}), 400
        
    print(f"\n📥 [Nova Mensagem do WhatsApp de {id_cliente}]: '{mensagem_cliente}'")
    
    # 1. Recupera o histórico do banco de dados SQLite para esse número específico
    historico = obter_historico_mensagens_sqlite(id_cliente)
    
    # 2. Registra a nova mensagem do usuário no histórico em memória e no banco
    historico.append(HumanMessage(content=mensagem_cliente))
    salvar_mensagem_sqlite(id_cliente, "user", mensagem_cliente)
    
    # 3. Executa o loop do agente de Inteligência Artificial com as ferramentas
    limite_rodadas = 0
    while limite_rodadas < 5:
        mensagens_input = [("system", prompt_sistema)] + historico
        resposta_ia = modelo_com_ferramentas.invoke(mensagens_input)
        
        if not resposta_ia.tool_calls:
            historico.append(resposta_ia)
            break
            
        historico.append(resposta_ia)
        limite_rodadas += 1
        
        for chamada in resposta_ia.tool_calls:
            nome_func = chamada["name"]
            argumentos = chamada["args"]
            id_chamada = chamada["id"]
            
            print(f"⚡ [NÓ n8n: {nome_func} -> Executando com {argumentos}...]")
            ferramenta_alvo = dicionario_de_ferramentas[nome_func]
            resultado_fisico = ferramenta_alvo.invoke(argumentos)
            
            historico.append(ToolMessage(content=str(resultado_fisico), tool_call_id=id_chamada))
            
    # 4. Salva a resposta final do robô no banco de dados SQLite para a próxima conversa
    salvar_mensagem_sqlite(id_cliente, "assistant", resposta_ia.content)
    print(f"📤 [Resposta do Atendente enviada]: {resposta_ia.content}\n")
    
    # Retorna o JSON exato contendo o texto da resposta para o integrador enviar ao WhatsApp
    return jsonify({
        "status": "sucesso",
        "to": id_cliente,
        "reply": resposta_ia.content
    }), 200

if __name__ == "__main__":
    print("\n🚀 [SERVIDOR WEB ATIVO] O seu Endpoint do WhatsApp está rodando localmente na porta 5000!")
    print("➔ URL do Webhook Local: http://localhost:5000/webhook\n")
    app.run(port=5000, debug=False)
