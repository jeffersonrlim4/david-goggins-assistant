import openai
from flask import Flask, jsonify, request
from dotenv import dotenv_values
import requests

config = dotenv_values(".env")

client = openai.Client(api_key=config['OPENAI_API_KEY'])

app = Flask(__name__)

base_url = config['ZAPI_BASE_URL']
headers = {
  "Client-Token": config['ZAPI_SECURITY_TOKEN']
}

content_system = '''
  Você é um assitente de corrida chamado David Goggins. 
  Você é sempre formal e qualquer coisa que te é perguntado você responde de 
  maneira séria e sempre leva a conversa para o lado da corrida.
  na primeira interação você fala seu nome, faz uma saudação e pergunta o nome da pessoa.
  ao final de cada resposta você fala uma frase motivacional curta
''' 

local_cache = {}

def generate_text_openai(messages, phone, model='gpt-4o-mini', max_tokens=1000, temperature=0):
  response = client.chat.completions.create(messages=messages, 
                                            model=model, 
                                            max_tokens=max_tokens, 
                                            temperature=temperature
                                          )
  chat_response_dict = response.choices[0].message.model_dump(exclude_none=True)
  
  local_cache[phone].append(chat_response_dict)
  
  content_message = response.choices[0].message.content
  return content_message

def send_message(phone, message):
  payload = {
        "phone": phone,
        "message": message,
        "delayTyping": 3
      }
  response = requests.post(f'{base_url}/send-text', json=payload, headers=headers)
  return response.json()
  

@app.route('/receive', methods=["POST"])
def receive_message():
  data = request.json
  
  if data['text']:
  
      print(data)
      
      phone = data['phone']
      message = data['text']['message']
      
      if phone not in local_cache:
        local_cache[phone] = [{'role': 'system', 'content': content_system}]
      
      local_cache[phone].append({'role': 'user', 'content': message})
      
      openai_text = generate_text_openai(local_cache[phone], phone)
      
      send_message(phone, openai_text)
      
      return jsonify({"data": local_cache[phone]})
  
  return jsonify({"message": "Is not a private mensage"}), 400

if __name__ == '__main__':
  app.run(debug=True)