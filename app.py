import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
# Importações modernas de memória e templates do LangChain
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ##############################################################################
# 1. ARQUITETURA DE NEGÓCIO: BANCO DE MEMÓRIA GLOBAL (ESCALÁVEL PARA WHATSAPP)
# ##############################################################################
if "banco_de_memorias" not in st.session_state:
    st.session_state.banco_de_memorias = {}

def obter_historico_sessao(session_id: str) -> BaseChatMessageHistory:
    """Recupera o histórico exclusivo de cada cliente com base no ID da sessão."""
    if session_id not in st.session_state.banco_de_memorias:
        st.session_state.banco_de_memorias[session_id] = InMemoryChatMessageHistory()
    return st.session_state.banco_de_memorias[session_id]

# ##############################################################################
# 2. INICIALIZAÇÃO DO CORE DE INTELIGÊNCIA ARTIFICIAL E PROMPT
# ##############################################################################
load_dotenv()

@st.cache_resource
def inicializar_ia():
    chave_secreta = os.getenv("GROQ_API_KEY")
    modelo = ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=chave_secreta,
        temperature=0.3
    )
    
    # Criamos o esqueleto do chat: System Prompt + Histórico + Nova Pergunta
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um atendente comercial inteligente e prestativo focado em ajudar clientes pelo WhatsApp de forma clara, objetiva e profissional."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    
    # Encadeia o prompt ao modelo de linguagem
    cadeia_ia = prompt | modelo
    
    # Envelopa toda a estrutura com o motor de gerenciamento de histórico
    modelo_com_memoria = RunnableWithMessageHistory(
        cadeia_ia,
        get_session_history=obter_historico_sessao,
        input_messages_key="input",
        history_messages_key="history"
    )
    return modelo_com_memoria

cerebro_ia = inicializar_ia()

# ##############################################################################
# 3. INTERFACE DE TESTES DO PRODUTO (STREAMLIT)
# ##############################################################################
st.set_page_config(page_title="Agente Comercial Core", page_icon="🤖")
st.title("🤖 Atendente Inteligente - Core v1.0")
st.write("---")

# ID de simulação de um cliente do WhatsApp
ID_CLIENTE_WHATSAPP = "cliente_teste_vagner"

# Recupera o histórico do cliente ativo
historico_atual = obter_historico_sessao(ID_CLIENTE_WHATSAPP)

# Renderiza as conversas antigas mantendo a interface limpa
for msg in historico_atual.messages:
    tipo_usuario = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(tipo_usuario):
        st.write(msg.content)

# Entrada de dados do usuário
comando_usuario = st.chat_input("Digite sua mensagem para o atendente comercial...")

if comando_usuario:
    # Exibe a pergunta do usuário na interface
    with st.chat_message("user"):
        st.write(comando_usuario)

    # Aciona a IA para processar a resposta consultando a memória do ID passado
    with st.chat_message("assistant"):
        with st.spinner("Respondendo ao cliente..."):
            
            resposta_da_ia = cerebro_ia.invoke(
                {"input": comando_usuario},
                config={"configurable": {"session_id": ID_CLIENTE_WHATSAPP}}
            )
            
            st.write(resposta_da_ia.content)
