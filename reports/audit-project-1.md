# ARCHITECTURE AUDIT REPORT

- Project: code-smells-project
- Stack: Python + Flask 3.1.1
- Files: 4 analyzed | 780 lines
- Architecture: Monolítica — HTTP, SQL e regra de negócio em `app.py`, `controllers.py`, `models.py` e `database.py`
- DB: SQLite (`loja.db`) | tables: produtos, usuarios, pedidos, itens_pedido

## Summary

CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] SQL concatenada nas queries de domínio — AP-01
- File: models.py:28
- Description: O id, o nome, o e-mail, a senha e os filtros de busca entram no texto SQL por concatenação. O mesmo padrão está em `models.py:47-50`, `57-61`, `67`, `91`, `109-111`, `126-129`, `140`, `148-166`, `174`, `188`, `192`, `279-281` e `289-297`.
- Evidence: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
- Impact: Qualquer campo de produto, usuário, login ou busca altera a query. Dá para ler a tabela de senhas ou apagar linhas.
- Recommendation: Trocar cada concatenação por `?` e uma tupla de parâmetros. Filtro dinâmico só acrescenta cláusula fixa.
- Playbook: PB-01

### [CRITICAL] Rota executa SQL enviado pelo cliente — AP-01
- File: app.py:69
- Description: `POST /admin/query` lê `sql` do JSON e chama `cursor.execute` com essa string. `SELECT` devolve as linhas; qualquer outro comando faz commit.
- Evidence: `cursor.execute(query)`
- Impact: Quem alcança a porta administra o banco. Não há allowlist nem autenticação.
- Recommendation: Manter `POST /admin/query` e o formato `{"erro": ...}`. Recusar a execução de SQL do cliente com 400.
- Playbook: PB-01

### [CRITICAL] Segredo no fonte e de novo no health — AP-02
- File: app.py:7
- Description: `SECRET_KEY` está fixa no entry point. `DEBUG` está fixo na linha 8. O health devolve a mesma chave em `controllers.py:289`. O processo sobe em `0.0.0.0` com `debug=True` em `app.py:88`.
- Evidence: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`
- Impact: O segredo fica no git e na resposta de `/health`. Com o debugger do Werkzeug exposto, a chave deixa de ser o único problema.
- Recommendation: Ler `SECRET_KEY`, `DEBUG`, host e porta de um módulo de config. Tirar `secret_key` do JSON do health.
- Playbook: PB-02

### [CRITICAL] God module com quatro domínios — AP-03
- File: models.py:1-314
- Description: Um módulo concentra SQL, mapeamento e regra de produto, usuário, pedido e relatório de vendas, inclusive estoque e alíquota de desconto.
- Evidence: `def relatorio_vendas():`
- Impact: Não existe teste de um domínio sem carregar os outros. Uma correção de pedido atravessa o arquivo inteiro.
- Recommendation: Um model por entidade e um controller por caso de uso. A rota só registra o caminho.
- Playbook: PB-03

### [CRITICAL] Senha em texto puro, gravada e devolvida — AP-04
- File: models.py:83
- Description: `get_todos_usuarios` e `get_usuario_por_id` devolvem a coluna `senha`. O insert de `models.py:126-129` grava a senha recebida. O seed em `database.py:76-78` grava `admin123`, `123456` e `senha123`.
- Evidence: `"senha": row["senha"],`
- Impact: `GET /usuarios` entrega a senha de cada conta. Cópia do `loja.db` revela as mesmas senhas.
- Recommendation: Gravar hash, aceitar a senha atual no login por compatibilidade e parar de serializar `senha`.
- Playbook: PB-07

### [HIGH] Conexão SQLite global e compartilhada entre threads — AP-06
- File: database.py:4-10
- Description: `db_connection` é global, criada uma vez e reutilizada com `check_same_thread=False`. O schema e o seed rodam dentro desse getter.
- Evidence: `db_connection = sqlite3.connect(db_path, check_same_thread=False)`
- Impact: Requests dividem a mesma conexão. O flag existe para calar o SQLite, não para isolar o estado.
- Recommendation: Abrir a conexão em `flask.g` e fechar no teardown. Seed no boot, não no import.
- Playbook: PB-06

### [HIGH] Regra de pedido e notificação dentro do controller HTTP — AP-05
- File: controllers.py:188-250
- Description: `criar_pedido` valida o payload, chama a regra e ainda dispara e-mail, SMS e push por `print`. `atualizar_status_pedido` decide notificação pelo status novo.
- Evidence: `print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado para usuario " + str(usuario_id))`
- Impact: A regra de pedido só existe atrás de `request`. O efeito colateral não tem fronteira para teste.
- Recommendation: Controller de caso de uso recebe um dict e devolve corpo e status. A view só faz `get_json` e `jsonify`. O log de notificação permanece log.
- Playbook: PB-04

### [HIGH] Reset do banco sem fronteira de autorização — AP-07
- File: app.py:47-57
- Description: `POST /admin/reset-db` apaga `itens_pedido`, `pedidos`, `produtos` e `usuarios`. Nenhuma rota do projeto lê sessão, token ou papel.
- Evidence: `cursor.execute("DELETE FROM usuarios")`
- Impact: Um POST anônimo zera a loja.
- Recommendation: Registrar o achado. Na Fase 3, não inventar 401 que mude o contrato desta rota; a correção obrigatória de privilégio é o fechamento do SQL livre em `/admin/query`.
- Playbook: PB-12

### [MEDIUM] N+1 ao montar pedido, item e produto — AP-08
- File: models.py:186-193
- Description: `get_pedidos_usuario` e `get_todos_pedidos` (`models.py:219-224`) buscam os itens de cada pedido e, para cada item, o nome do produto.
- Evidence: `cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))`
- Impact: Três idas ao banco por item. O custo cresce com pedidos × itens, e a query continua concatenada.
- Recommendation: Uma consulta com `JOIN` e `IN` parametrizado, agrupando itens em memória.
- Playbook: PB-05

### [MEDIUM] Validação de produto copiada em criar e atualizar — AP-09
- File: controllers.py:31-50
- Description: Presença de nome, preço e estoque, limites de tamanho e preço negativo estão repetidos em `atualizar_produto` (`controllers.py:74-90`). A lista de categorias válidas só existe no criar.
- Evidence: `if "nome" not in dados:`
- Impact: Uma regra nova de produto precisa ser editada duas vezes e a atualização já divergiu (não valida categoria).
- Recommendation: Uma função de validação usada pelas duas operações, com as mesmas mensagens.
- Playbook: PB-10

### [MEDIUM] Exceção interna vira corpo HTTP — AP-11
- File: controllers.py:11-12
- Description: Cada função da borda captura `Exception` e devolve `str(e)` com 500. Em `login` (`controllers.py:169-170`), body nulo cai nesse caminho porque o código chama `.get` sem testar `dados`.
- Evidence: `return jsonify({"erro": str(e)}), 500`
- Impact: Erro de SQL e `AttributeError` saem para o cliente. Não há um formato único de falha.
- Recommendation: Validação de negócio continua explícita. O resto sobe para um error handler com mensagem genérica.
- Playbook: PB-09

### [LOW] Alíquotas mágicas no relatório de vendas — AP-12
- File: models.py:257-262
- Description: Limiares `10000`, `5000` e `1000` e taxas `0.1`, `0.05` e `0.02` estão soltos dentro de `relatorio_vendas`.
- Evidence: `desconto = faturamento * 0.1`
- Impact: A regra de desconto não tem nome. Mudar a faixa exige ler o miolo da função.
- Recommendation: Constantes ao lado do cálculo, com os mesmos números.
- Playbook: PB-11

### [LOW] Log por concatenação e import morto — AP-12
- File: controllers.py:8
- Description: O fluxo feliz imprime com concatenação. `models.py:2` importa `sqlite3` e não usa.
- Evidence: `print("Listando " + str(len(produtos)) + " produtos")`
- Impact: Ruído de leitura. Não muda o desenho.
- Recommendation: Limpar só os arquivos já tocados por outro playbook.
- Playbook: PB-11

## Deprecated APIs

- Varredura AP-10 executada. Nenhuma API obsoleta do catálogo neste projeto.

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
