import os
import unicodedata
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# ##############################################################################
# NÓ 1: BANCO DE DADOS DE MEMÓRIA (Histórico de Conversas Isolado)
# ##############################################################################
if "banco_de_memorias" not in locals():
    banco_de_memorias = {}

def obter_historico_mensagens(session_id: str):
    if session_id not in banco_de_memorias:
        banco_de_memorias[session_id] = []
    return banco_de_memorias[session_id]

load_dotenv()

# ##############################################################################
# NÓ 2: AS FERRAMENTAS DO ROBÔ (Consulta de Estoque e Calculadora)
# ##############################################################################
def remover_acentos(texto: str) -> str:
    """Remove acentos e deixa o texto limpo para busca exata (Ex: tênis -> tenis)."""
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")

@tool
def buscar_produto_ou_promocao(nome_produto: str) -> str:
    """Busca o preço, estoque ou promoções de um produto na planilha da loja."""
    estoque_simulado = {
        "camisa": "Camisa Polo Oficial - Preço: R$ 89,90 | Estoque: 15 unidades | Promoção: Leve 3 por R$ 240,00",
        "tenis": "Tênis Running Sport - Preço: R$ 199,90 | Estoque: 4 unidades | Sem promoções ativas",
        "bone": "Boné Aba Curva Street - Preço: R$ 45,00 | Estoque: 0 unidades (Esgotado)"
    }
    
    # Remove acentos e espaços extras da busca do cliente
    produto_limpo = remover_acentos(nome_produto.lower().strip())
    
    for chave in estoque_simulado:
        if chave in produto_limpo or produto_limpo in chave:
            return estoque_simulado[chave]
            
    return f"Produto '{nome_produto}' não encontrado. Temos disponíveis apenas: camisa, tenis e bone."

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
# NÓ 3: CORE DO MENSAGEIRO E MODELO DE INTELIGÊNCIA ARTIFICIAL
# ##############################################################################
modelo_base = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)

modelo_com_ferramentas = modelo_base.bind_tools(list(dicionario_de_ferramentas.values()))

prompt_sistema = """Você é um Atendente Comercial de WhatsApp sênior e automatizado.
Sua missão é responder o cliente com base estritamente nas informações retornadas pelas ferramentas.

REGRAS DE OURO:
1. Você está PROIBIDO de chamar a mesma ferramenta com o mesmo argumento mais de uma vez se ela já retornou um resultado.
2. Se a ferramenta disser que o produto não foi encontrado ou der os valores, leia o texto de retorno e responda diretamente ao cliente o que a ferramenta informou.
3. Se o cliente pedir para calcular ou fechar o pedido com cupom, use a ferramenta 'calcular_orcamento_com_desconto'.
"""

# ##############################################################################
# 4. AMBIENTE DE TESTES DO AGENTE VIA TERMINAL
# ##############################################################################
if __name__ == "__main__":
    print("\n🤖 [NÓ ATIVO] Atendente de WhatsApp Inteligente Online!")
    print("Digite 'sair' para encerrar.\n")
    
    ID_CONVERSA_WHATSAPP = "telefone_cliente_vagner"
    historico = obter_historico_mensagens(ID_CONVERSA_WHATSAPP)
    
    while True:
        entrada_cliente = input("👤 Cliente WhatsApp: ")
        if entrada_cliente.lower() == "sair":
            break
            
        historico.append(HumanMessage(content=entrada_cliente))
        
        # Limitador de segurança para evitar loops infinitos de ferramentas da API
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
                
                print(f"📥 [Planilha retornou]: {resultado_fisico}")
                historico.append(ToolMessage(content=str(resultado_fisico), tool_call_id=id_chamada))
        
        print(f"🤖 Atendente:\n{resposta_ia.content}\n")
