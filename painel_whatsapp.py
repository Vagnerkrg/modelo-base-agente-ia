import streamlit as st
import requests

# Configuração da página visual
st.set_page_config(page_title="Simulador WhatsApp API", page_icon="💬", layout="centered")

st.title("💬 Simulador de Atendimento - WhatsApp API")
st.write("Esta interface visual simula o envio de mensagens do celular do cliente direto para a sua API Flask (Porta 5000).")
st.write("---")

# URL oficial do seu servidor Flask que está rodando em background
URL_API = "http://localhost:5000/webhook"
NUMERO_CLIENTE = "5521999999999"

# Inicializa o histórico visual na tela do Streamlit se não existir
if "mensagens_tela" not in st.session_state:
    st.session_state.mensagens_tela = []

# Renderiza o chat bonito na tela
for msg in st.session_state.mensagens_tela:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Caixa de digitação do cliente no navegador
entrada_usuario = st.chat_input("Envie uma mensagem simulando o WhatsApp do cliente...")

if entrada_usuario:
    # 1. Mostra a mensagem do usuário na tela
    with st.chat_message("user"):
        st.write(entrada_usuario)
    st.session_state.mensagens_tela.append({"role": "user", "content": entrada_usuario})
    
    # 2. Dispara os dados em JSON para o seu servidor Flask em background (Igual o WhatsApp faz!)
    with st.chat_message("assistant"):
        with st.spinner("IA processando nós de estoque e calculadora..."):
            try:
                payload = {"from": NUMERO_CLIENTE, "message": entrada_usuario}
                resposta = requests.post(URL_API, json=payload)
                
                if resposta.status_code == 200:
                    texto_ia = resposta.json().get("reply", "")
                    st.write(texto_ia)
                    st.session_state.mensagens_tela.append({"role": "assistant", "content": texto_ia})
                else:
                    st.error(f"Erro no servidor: {resposta.status_code}")
            except Exception as e:
                st.error("Erro: Garanta que o servidor 'agente_comercial.py' esteja rodando no outro terminal!")
