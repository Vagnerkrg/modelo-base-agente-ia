import streamlit as st
import os
from dotenv import load_dotenv
# Mudamos para o conector nativo e oficial da Groq
from langchain_groq import ChatGroq

# 1. Carrega a chave secreta do arquivo .env com total segurança
load_dotenv()

# 2. Configura a página web do seu Agente
st.set_page_config(page_title="Agente Inteligente", page_icon="🤖")

st.title("🤖 Meu Primeiro Agente de IA")
st.write("---")
st.write("Bem-vindo! Pergunte qualquer coisa e eu responderei usando inteligência artificial de alta velocidade.")

# 3. LIGA O CÉREBRO DO ROBÔ (Usando o conector direto e oficial da Groq)
@st.cache_resource
def inicializar_ia():
    chave_secreta = os.getenv("GROQ_API_KEY")
    
    # Atualizado para o modelo ativo e ultraveloz da Groq
    return ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=chave_secreta
    )


cerebro_ia = inicializar_ia()

# 4. Caixinha de chat para o usuário digitar
comando_usuario = st.chat_input("Digite sua mensagem para o agente...")

if comando_usuario:
    # Mostra o que você digitou na tela
    with st.chat_message("user"):
        st.write(comando_usuario)
        
    # Aciona a Inteligência Artificial para pensar e responder em tempo real
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Envia a pergunta diretamente para os servidores da Groq
            resposta_da_ia = cerebro_ia.invoke(comando_usuario)
            # Imprime a resposta inteligente do robô na tela
            st.write(resposta_da_ia.content)
