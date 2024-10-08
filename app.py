from flask import Flask, render_template, request, session
from openai import OpenAI
from dotenv import load_dotenv
import os
from time import sleep
from helpers import *
from assistente import *

load_dotenv()

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = os.getenv("MODELO_GERAL")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_KEY")

# Removed the global thread variable
# thread = criar_thread()

entrevistador = "asst_B7cRi6e9O0VV6bACSS6Bn0wA"  # Asistente Entrevistador 2 (OpenaAI Bicalho)
redator = "asst_MQj0jeIAzuRnYI8bMdCx8hv1"  # Redator IART5

# Removed the global assistente variable
# assistente = entrevistador

def bot(prompt):
    # Retrieve or create thread per user session
    if 'thread_id' not in session:
        # Create a new thread
        thread = cliente.beta.threads.create()
        session['thread_id'] = thread.id
    else:
        thread_id = session['thread_id']
        thread = cliente.beta.threads.retrieve(thread_id=thread_id)

    # Retrieve or set assistant per user session
    if 'assistente' not in session:
        session['assistente'] = entrevistador  # Initial assistant
    assistente = session['assistente']

    # Get the conversation history
    historico = list(cliente.beta.threads.messages.list(thread_id=thread.id).data)

    if len(historico) > 0:
        ultima_interacao = historico[0].content[0].text.value

        if "FIM DA ENTREVISTA" in ultima_interacao:
            session['assistente'] = redator
            assistente = redator

            # Create a message from the redator
            cliente.beta.threads.messages.create(
                thread_id=thread.id,
                role="assistant",
                content="Olá, sou o redator. Vou agora escrever o critério baseado nas informações fornecidas."
            )

            run = cliente.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistente
            )

            while run.status != "completed":
                run = cliente.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

            historico = list(cliente.beta.threads.messages.list(thread_id=thread.id).data)
            resposta = historico[0]
            return resposta

    maximo_tentativas = 1
    repeticao = 0

    while True:
        try:
            cliente.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            run = cliente.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistente
            )

            while run.status != "completed":
                run = cliente.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

            historico = list(cliente.beta.threads.messages.list(thread_id=thread.id).data)
            resposta = historico[0]
            return resposta

        except Exception as erro:
            repeticao += 1
            if repeticao >= maximo_tentativas:
                return f"Erro no GPT: {erro}"
            print('Erro de comunicação com OpenAI: ', erro)
            sleep(1)

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.json["msg"]
    resposta = bot(prompt)
    print(resposta)
    texto_resposta = resposta.content[0].text.value
    return texto_resposta

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)