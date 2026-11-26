# ARCHITECTURE AUDIT REPORT

- Project: code-smells-project
- Stack: Python + Flask 3.1.1
- Files: 4 analyzed | 780 lines
- Architecture: Monolítica
- DB: SQLite (`loja.db`) | tables: `produtos`, `usuarios`, `pedidos`, `itens_pedido`

## Summary

CRITICAL: 6 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Execução de SQL arbitrário enviado pelo cliente em `/admin/query` — AP-01
- File: app.py:69
- Description: A rota `POST /admin/query` (linhas 59-78) lê o campo `sql` diretamente do JSON recebido (linha 62) e o repassa sem validação para `cursor.execute(query)` (linha 69), executando qualquer comando `SELECT`, escrita ou DDL enviado pelo cliente.
- Evidence: `cursor.execute(query)`
- Impact: Permite leitura, alteração ou destruição arbitrária de qualquer tabela do banco de dados fora do contrato da aplicação.
- Recommendation: Remover a execução de SQL livre fornecido pelo cliente, recusando comandos SQL arbitrários com status `400`, e restringir a rota com autenticação administrativa.
- Playbook: PB-01

### [CRITICAL] Concatenação de parâmetros em consultas SQL na camada de modelos — AP-01
- File: models.py:110
- Description: Funções de persistência em `models.py` concatenam parâmetros diretamente no texto das queries SQL em `login_usuario` (linhas 109-111), `get_produto_por_id` (linha 28), `criar_produto` (linhas 47-50), `atualizar_produto` (linhas 57-61), `deletar_produto` (linha 68), `get_usuario_por_id` (linha 92), `criar_usuario` (linhas 126-129), `criar_pedido` (linhas 140, 148-151, 155, 157-166), `get_pedidos_usuario` (linhas 174, 188, 192), `get_todos_pedidos` (linhas 220, 224), `atualizar_status_pedido` (linhas 279-281) e `buscar_produtos` (linhas 291-299).
- Evidence: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`
- Impact: Expõe a aplicação a SQL Injection, permitindo bypass de autenticação no login, exfiltração de dados e manipulação indevida de registros.
- Recommendation: Substituir todas as concatenações de SQL por consultas parametrizadas usando placeholders `?` e tuplas de parâmetros em `cursor.execute`.
- Playbook: PB-01

### [CRITICAL] `SECRET_KEY` hardcoded no código e exposta na resposta de `/health` — AP-02
- File: controllers.py:289
- Description: A chave secreta `"minha-chave-super-secreta-123"` está hardcoded em `app.py:7` (`app.config["SECRET_KEY"]`) e é retornada literalmente no JSON público da rota `GET /health` em `controllers.py:289`, junto com `db_path` e `debug` (linhas 287-288).
- Evidence: `"secret_key": "minha-chave-super-secreta-123"`
- Impact: Qualquer cliente que consulte `/health` obtém a chave secreta da aplicação, comprometendo integridade de sessões e tokens assinados, além de manter segredo versionado no repositório.
- Recommendation: Centralizar `SECRET_KEY` e demais configurações em módulo de config lido de variáveis de ambiente (documentado em `.env.example`) e remover `secret_key`, `db_path` e `debug` da resposta de `/health`.
- Playbook: PB-02

### [CRITICAL] Senhas armazenadas em texto puro e expostas nas respostas de usuários — AP-04
- File: models.py:128
- Description: As senhas de usuários são gravadas em texto puro tanto no seed inicial (`database.py:75-83`) quanto em `criar_usuario` (`models.py:126-129`), comparadas em texto puro em `login_usuario` (`models.py:109-111`), e devolvidas no JSON de `get_todos_usuarios` (`models.py:83`) e `get_usuario_por_id` (`models.py:99`).
- Evidence: `"senha": row["senha"],`
- Impact: Qualquer requisição a `GET /usuarios` ou `GET /usuarios/<id>`, ou leitura do arquivo `loja.db`, revela diretamente as senhas de todos os usuários, incluindo o administrador.
- Recommendation: Armazenar senhas com hash seguro (`werkzeug.security.generate_password_hash`), validar credenciais no login via `check_password_hash` e remover o campo `senha` da serialização de usuários.
- Playbook: PB-07

### [CRITICAL] God module em `models.py` acumulando persistência e regras de negócio de todo o domínio — AP-03
- File: models.py:1-314
- Description: Um único módulo de 314 linhas concentra queries SQL, mapeamento de registros e regras de negócio (validação de estoque, cálculo de total e baixa de estoque em `criar_pedido` linhas 133-169; faixas de desconto e ticket médio em `relatorio_vendas` linhas 235-273) para quatro entidades (`produtos`, `usuarios`, `pedidos` e `itens_pedido`).
- Evidence: `def relatorio_vendas():`
- Impact: Impede testar ou evoluir um domínio isoladamente e faz com que qualquer mudança de regra ou persistência atravesse o arquivo inteiro.
- Recommendation: Dividir `models.py` em modelos/repositórios por entidade (`produto`, `usuario`, `pedido`, `relatorio`) e mover regras de negócio para a camada de controllers/serviços.
- Playbook: PB-03

### [CRITICAL] God module em `controllers.py` acumulando borda HTTP, validação, regras, notificações e SQL direto — AP-03
- File: controllers.py:1-292
- Description: Um único módulo de 292 linhas concentra 16 handlers HTTP de todos os recursos da API (`produtos`, `usuarios`, `login`, `pedidos`, `relatorios` e `health`), misturando parsing de requisição, validação de domínio, notificações (`print` nas linhas 208-210 e 247-250) e execução direta de SQL via `get_db()` em `health_check` (linhas 266-274).
- Evidence: `from database import get_db`
- Impact: Forte acoplamento entre domínios e camada HTTP dificulta testes unitários isolados e aumenta o risco de regressões em alterações rotineiras.
- Recommendation: Separar `controllers.py` em blueprints de rotas e controllers por recurso de domínio, removendo qualquer consulta SQL direta da camada de controller.
- Playbook: PB-03

### [HIGH] Rotas administrativas e destrutivas expostas sem autenticação ou autorização — AP-07
- File: app.py:47-57
- Description: O projeto não possui nenhuma função de autenticação ou autorização; as rotas administrativas `POST /admin/reset-db` (`app.py:47-57`), `POST /admin/query` (`app.py:59-78`), `GET /relatorios/vendas` (`app.py:28`, `controllers.py:257-262`) e a remoção `DELETE /produtos/<int:id>` (`app.py:16`, `controllers.py:98-109`) aceitam chamadas anônimas sem verificação de credencial ou papel.
- Evidence: `@app.route("/admin/reset-db", methods=["POST"])`
- Impact: Qualquer cliente anônimo pode apagar todas as tabelas do banco, excluir produtos do catálogo ou acessar o faturamento consolidado da loja.
- Recommendation: Emitir token assinado no endpoint `/login` e proteger as rotas administrativas e destrutivas com decorator de autorização (`401` sem credencial válida e `403` para usuário sem papel administrativo).
- Playbook: PB-12

### [HIGH] Entrypoint `app.py` executa SQL direto e lógica administrativa nas rotas — AP-05
- File: app.py:47-78
- Description: O arquivo de entrada `app.py` mistura bootstrap da aplicação com rotas administrativas (`reset_database` nas linhas 47-57 e `executar_query` nas linhas 59-78) que abrem conexão com `get_db()` e executam comandos `DELETE` e SQL diretamente no banco.
- Evidence: `cursor.execute("DELETE FROM itens_pedido")`
- Impact: Acopla a inicialização da aplicação a operações de persistência e dificulta testar ou isolar o fluxo administrativo.
- Recommendation: Mover as rotas administrativas para um blueprint e controller dedicados, deixando `app.py` restrito à app factory, configuração e registro de rotas.
- Playbook: PB-04

### [HIGH] Handlers HTTP em `controllers.py` misturam validação de domínio, notificações e SQL direto — AP-05
- File: controllers.py:52
- Description: Funções ligadas diretamente às rotas em `controllers.py` executam validação de regras de negócio (`criar_produto` linhas 43-54, `atualizar_produto` linhas 87-90, `atualizar_status_pedido` linha 242), disparo de notificações (`criar_pedido` linhas 208-210 e `atualizar_status_pedido` linhas 247-250) e acesso direto ao SQLite (`health_check` linhas 266-274).
- Evidence: `categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]`
- Impact: Regras de negócio não podem ser reutilizadas nem testadas sem simular requisições HTTP.
- Recommendation: Manter as rotas apenas para encaminhamento HTTP, extrair validadores e serviços de domínio e delegar as consultas de `health_check` à camada de banco/modelo.
- Playbook: PB-04

### [HIGH] Conexão SQLite global mutável compartilhada entre threads com `check_same_thread=False` — AP-06
- File: database.py:10
- Description: `database.py` armazena a conexão em variável global mutável `db_connection` (linhas 4 e 8-9) criada com `sqlite3.connect(db_path, check_same_thread=False)` (linha 10), além de criar o schema e rodar o seed dentro de `get_db()` na primeira requisição (linhas 14-84).
- Evidence: `db_connection = sqlite3.connect(db_path, check_same_thread=False)`
- Impact: Requisições concorrentes compartilham a mesma conexão e transação SQLite, causando vazamento de estado entre testes e risco de condições de corrida.
- Recommendation: Gerenciar uma conexão SQLite por requisição via `flask.g` com fechamento em `teardown_appcontext` e extrair `init_db()` para inicialização explícita no boot.
- Playbook: PB-06

### [MEDIUM] `try/except Exception` repetido em todos os handlers vazando `str(e)` ao cliente — AP-11
- File: controllers.py:12
- Description: Todos os 16 handlers em `controllers.py` (linhas 10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292) e `executar_query` em `app.py:77-78` repetem blocos `try/except Exception as e` que retornam `str(e)` na resposta `500`, com formatos de erro inconsistentes entre endpoints.
- Evidence: `return jsonify({"erro": str(e)}), 500`
- Impact: Expõe detalhes internos de exceções e do banco SQLite ao cliente, além de duplicar tratamento de erro e quebrar consistência do contrato de falhas.
- Recommendation: Remover os `try/except` repetitivos dos handlers, registrar handlers centralizados via `@app.errorhandler` e logar exceções internamente sem expor `str(e)` na resposta HTTP.
- Playbook: PB-09

### [MEDIUM] Consultas N+1 aninhadas ao listar pedidos e reconsulta de produtos em laço ao criar pedido — AP-08
- File: models.py:192
- Description: `get_pedidos_usuario` (`models.py:177-199`) e `get_todos_pedidos` (`models.py:209-232`) executam uma query de `itens_pedido` para cada pedido e outra query de `produtos` para cada item dentro de laços aninhados; além disso, `criar_pedido` (`models.py:139-166`) consulta cada produto duas vezes em laços separados.
- Evidence: `cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))`
- Impact: O volume de queries cresce proporcionalmente a pedidos × itens, degradando o tempo de resposta conforme a base aumenta.
- Recommendation: Substituir as consultas em laço na listagem de pedidos por `JOIN` único entre `pedidos`, `itens_pedido` e `produtos`, e reutilizar os produtos carregados na validação em `criar_pedido`.
- Playbook: PB-05

### [MEDIUM] Duplicação de lógica de validação de produto e de montagem/serialização de registros — AP-09
- File: controllers.py:72-90
- Description: O bloco de validação de produto está duplicado entre `criar_produto` (`controllers.py:28-54`) e `atualizar_produto` (`controllers.py:72-90`), já divergindo (a atualização omite validação de tamanho do nome e categorias válidas); em `models.py`, a serialização de produto se repete em três funções (linhas 12-21, 31-40 e 304-313) e o bloco de montagem de pedidos com itens está copiado entre `get_pedidos_usuario` (linhas 176-201) e `get_todos_pedidos` (linhas 208-233).
- Evidence: `if preco < 0:`
- Impact: Correções de validação ou mudanças de campos precisam ser aplicadas em múltiplos pontos, gerando comportamento inconsistente entre endpoints.
- Recommendation: Extrair um validador único de produto e helpers compartilhados de serialização/montagem para produtos, usuários e pedidos.
- Playbook: PB-10

### [LOW] Imports não utilizados em `database.py` e `models.py` — AP-12
- File: database.py:2
- Description: `database.py` importa `os` na linha 2 e `models.py` importa `sqlite3` na linha 2 sem utilizá-los em nenhum ponto do módulo.
- Evidence: `import os`
- Impact: Polui o cabeçalho dos módulos e dificulta identificar as dependências efetivas de cada arquivo.
- Recommendation: Remover os imports ociosos de ambos os arquivos.
- Playbook: PB-11

### [LOW] `print()` de debug no fluxo de requisições e números mágicos de regra sem constantes — AP-12
- File: models.py:257-262
- Description: O cálculo de desconto em `relatorio_vendas` (`models.py:257-262`) usa limiares (`10000`, `5000`, `1000`) e percentuais (`0.1`, `0.05`, `0.02`) literais sem constantes nomeadas; o mesmo ocorre para limites de nome (`2`, `200` em `controllers.py:47-50`), além de chamadas `print()` no fluxo feliz de requisições em `controllers.py` (linhas 8, 57, 106, 161, 179, 182, 208-210, 248, 250) e `app.py:56`.
- Evidence: `if faturamento > 10000:`
- Impact: Dificulta leitura e ajuste de parâmetros de negócio e mistura saída padrão com logging operacional.
- Recommendation: Extrair constantes nomeadas para regras de desconto e validação, e substituir chamadas `print()` por `logging`.
- Playbook: PB-11

## Deprecated APIs

- Varredura AP-10 executada. Nenhuma API obsoleta do catálogo neste projeto.

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
