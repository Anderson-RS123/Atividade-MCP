MCP Tools

Este projeto implementa um servidor MCP (Model Context Protocol) usando Python, integrando ferramentas personalizadas que podem ser chamadas por um modelo de IA (Gemini 2.5 Pro). Também inclui um cliente interativo que valida perguntas, escolhe a ferramenta correta via IA e executa a requisição no MCP Server.

🚀 Funcionalidades

Ferramentas disponíveis no servidor MCP:

🔮 Previsão do Tempo

Busca dados da API Open-Meteo, envia ao Gemini e retorna um JSON estruturado apenas para o dia solicitado.

🔗 Extração de Links

Recebe uma URL (somente https), coleta o HTML e retorna todos os links encontrados (sem duplicatas).

🔡 Contagem de Letra

Conta quantas vezes uma letra aparece em um texto.

🛡️ Guardrails

guardrail_pergunta: valida comandos perigosos, datas, URLs e formato da requisição.

guardrail_resposta: valida se a resposta da IA está em JSON correto.
