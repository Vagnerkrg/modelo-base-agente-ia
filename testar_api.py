import requests

url = "http://localhost:5000/webhook"
payload = {
    "from": "5521999999999",
    "message": "Bom dia! Quanto custa a camisa e o tenis? Calcula com o cupom VIP20."
}

print("📡 Enviando mensagem simulada de WhatsApp para o servidor...")
resposta = requests.post(url, json=payload)

print("\n📥 [RESPOSTA DO SERVIDOR EM JSON]:")
print(resposta.json())
