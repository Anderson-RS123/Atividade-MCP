
import asyncio
import json
import google.generativeai as genai
from mcp import ClientSession, types
from mcp.client.sse import sse_client


genai.configure(api_key="")  # insira a chave API

#modelo
MODEL = "gemini-2.5-pro"

async def run_tool_with_gemini(prompt: str):
    async with sse_client("http://localhost:8000/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Lista as ferramentas disponíveis no servidor
            tools = await session.list_tools()
            tool_schemas = [
                {"name": t.name, "description": t.description, "parameters": t.inputSchema}
                for t in tools.tools
            ]

            # guardrail de entrada
            print("Verificando entrada com guardrail_pergunta...")
            verif = await session.call_tool("guardrail_pergunta", {"prompt": prompt})
            for content in verif.content:
                if isinstance(content, types.TextContent):
                    if "OK" not in content.text:
                        print("Erro de validação:", content.text)
                        return  # para execução se a entrada for inválida
                    else:
                        print("Entrada validada com sucesso.")

            # prompt do usuario
            gemini_prompt = f"""
            You are an AI assistant connected to an MCP server with these tools:

            {json.dumps(tool_schemas, indent=2)}

            Based on this user request:
            "{prompt}"

            Respond ONLY in JSON with:
            {{
                "tool": "<tool_name>",
                "args": {{ ... arguments ... }}
            }}
            """

            model = genai.GenerativeModel(MODEL)
            response = model.generate_content(gemini_prompt)
            text = response.text.strip()

            # Remove wrappers de ```json ... ```
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:].strip()
                elif text.lower().startswith("json\n"):
                    text = text[5:].strip()

            try:
                choice = json.loads(text)
                tool_name = choice["tool"]
                args = choice.get("args", {})
            except Exception as e:
                print("Gemini parsing error:", e)
                print("Raw response text:", response.text)
                return

            print(f"Gemini escolheu: {tool_name}({args})")

            # execucao da tool escolhida
            result = await session.call_tool(tool_name, args)

            # guardrail de saida
            print("Verificando saída com guardrail_resposta...")
            for content in result.content:
                if isinstance(content, types.TextContent):
                    resposta = content.text
                    validacao = await session.call_tool("guardrail_resposta", {"resposta": resposta})
                    for v in validacao.content:
                        if isinstance(v, types.TextContent):
                            print("Resposta validada com sucesso.")
                    
                    # Exibe o resultado final para o usuário
                    print("\nResultado final:\n")
                    print(resposta)


if __name__ == "__main__":
    while True:
        user_prompt = input("Faça a sua pergunta: Você também pode personalizar a sua pergunta em 3 atividades especializadas: " \
        "\n1: Pedir a previsão do tempo de um dia específico para o Recanto Maestro. A data precisar ser: dd/mm/aaaa" \
        "\n2: Trazer uma lista das urls de uma url específica(apenas https)." \
        "\n3: Contar quantas vezes uma letra específica aparece em uma frase.\n")
        asyncio.run(run_tool_with_gemini(user_prompt))