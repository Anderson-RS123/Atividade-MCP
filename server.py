from mcp.server.fastmcp import FastMCP
import requests
import pywhatkit as kit
import re
import json
import datetime as dt

mcp = FastMCP("dataops", stateless_http=True)

@mcp.tool()
def previsao_do_tempo(dia: str, reverso: bool = False) -> str:
    url = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=-29.6977"
    "&longitude=-53.5209"
    "&current_weather=true"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "rain_sum,showers_sum,snowfall_sum,precipitation_hours,weathercode,"
    "uv_index_max,uv_index_clear_sky_max,wind_speed_10m_max,wind_gusts_10m_max,"
    "wind_direction_10m_dominant,shortwave_radiation_sum"
    "&timezone=America/Sao_Paulo"
    )

    # Faz a requisição para a API da previsão do tempo
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    #print(data)

    # Chave API para buscar a resposta do Gemini
    api_Key = "" 
            
    import google.generativeai as genai
    genai.configure(api_key=api_Key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    # Inicializa o histórico da conversa
    conversation_history = conversation_history = f'''Vou passar um arquivo txt de dados de uma previsão do tempo do Recanto Maestro. Faça um resumo 
    desses dados apenas do dia {dia}. Faça a análise dos seguintes dados meteorológicos: {data} e
    traga a previsão apenas para o dia {dia}. Quero apenas que faça a análise desse dia em específico, e traga o JSON no seguinte formato: {{
        "previsoes": [
            {{
                "dia": "",
                "temperatura": "",
                "Precipitação": "",
                "Condições": "",
                "Vento": "",
                "Radiação Solar": "",
                "Análise": ""
            }}
        ]
    }}'''

    user_input = conversation_history
    chat = model.start_chat(history=[]) 

    def generate_prompt(prompt):
        return f"{prompt}"

    # Envia e recebe a resposta da IA
    response = chat.send_message(generate_prompt(user_input), stream=True)
    analise_texto = ""
    for s in response:
        if s.text:
            analise_texto += s.text

    # retornar o texto da IA
    return analise_texto

@mcp.tool()
def extrair_links(url: str) -> list[str]:
    # Função que recebe a url mostra todos os links encontrados no html
    try:
        # faz requisição
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        
        # pega o html
        html = resposta.text
        
        # encontra links no html
        padrao = r'href=["\'](https?://[^"\']+)["\']'
        links = re.findall(padrao, html)
        
        # remover duplicados
        links_unicos = sorted(set(links))
        return links_unicos
    
    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")
        return []
    

@mcp.tool()
def contar_letra_especifica(texto: str, letra: str) -> int:
    texto = texto.lower()
    letra = letra.lower()
    return texto.count(letra)

@mcp.tool()
def guardrail_pergunta(prompt: str) -> str:
    # Verifica se a entrada do usuário é segura e válida.

    if not prompt.strip():
        return "Entrada vazia. Por favor, digite algo."

    # linguagem ofensiva / comandos perigosos
    proibidos = ["drop table", "delete from", "shutdown", "rm -rf", "hack", "injection"]
    if any(p in prompt.lower() for p in proibidos):
        return "Entrada contém comandos potencialmente perigosos."

    #verificação de URLs: permite https:// em qualquer parte do texto
    urls = re.findall(r'https?://[^\s\'"]+', prompt)
    if urls:
        for url in urls:
            if not url.startswith("https://"):
                return f"A URL deve começar com 'https://'. URL inválida: {url}"

    # Verificação de letra única (para a função contar_letra_especifica)
    if "contar" in prompt.lower():
        # Captura qualquer conteúdo entre aspas simples ou duplas
        partes = re.findall(r"['\"](.*?)['\"]", prompt)

        # Se encontrou alguma coisa entre aspas
        if partes:
            letra = partes[0].strip()

            # Depuração opcional (mostra o que foi capturado)
            print(f"[DEBUG] Letra capturada: '{letra}'")

            if len(letra) != 1:
                return "Informe apenas uma letra única."
        else:
            return "Informe a letra entre aspas simples ou duplas."
        
    # Verificação de data no formato dd/mm/aaaa
    datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", prompt)
    if datas:
        for data_str in datas:
            try:
                dt.datetime.strptime(data_str, "%d/%m/%Y")
            except ValueError:
                return f"Data inválida: {data_str}. Use o formato correto dd/mm/aaaa."
    elif "previsão" in prompt.lower() or "tempo" in prompt.lower():
        # Se for uma pergunta sobre previsão e não houver data
        return "⚠️ Por favor, informe a data no formato dd/mm/aaaa."
    
    return "OK"

@mcp.tool()
def guardrail_resposta(resposta: str) -> str:
    #Verifica se a resposta da IA está no formato correto.
  
    if not resposta.strip():
        return "Resposta vazia da IA."

    data = json.loads(resposta)

    # verificar se campos esperados estão presentes
    if "previsoes" in data:
        esperado = {"dia", "temperatura", "Precipitação", "Condições", "Vento", "Radiação Solar", "Análise"}
        for item in data["previsoes"]:
            faltando = esperado - set(item.keys())
            if faltando:
                return f"Faltam campos no JSON: {faltando}"

    return "OK"


if __name__ == "__main__":
    print("MCP run")
    mcp.run()