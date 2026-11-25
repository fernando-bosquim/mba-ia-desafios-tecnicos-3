# ARCHITECTURE AUDIT REPORT

- Project: task-manager-api
- Stack: Python + Flask 3.0.0 e Flask-SQLAlchemy 3.1.1
- Files: 12 analyzed | 1155 lines
- Architecture: Camadas parciais — `models/`, `routes/`, `services/` e `utils/` existem; a rota ainda concentra validação, ORM e regra
- DB: SQLite (`tasks.db`) | tables: users, tasks, categories

## Summary

CRITICAL: 2 | HIGH: 3 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Senha com MD5 e hash na resposta — AP-04
- File: models/user.py:29
- Description: `set_password` e `check_password` usam MD5 sem sal. `to_dict` inclui `password` (`models/user.py:21`). O login devolve esse dict e ainda um token fictício em `routes/user_routes.py:207-210`. O seed grava senhas curtas (`1234`, `abcd`, `pass`) por esse mesmo método.
- Evidence: `self.password = hashlib.md5(pwd.encode()).hexdigest()`
- Impact: A resposta de login e de `GET /users/<id>` entrega o hash. MD5 sem sal se reverte com tabela pré-calculada, e as senhas do seed são curtas.
- Recommendation: `generate_password_hash` do Werkzeug, com aceitação do MD5 antigo no login para não quebrar o seed. Tirar `password` de todo dict público.
- Playbook: PB-07

### [CRITICAL] Segredos fixos no entry point e no SMTP — AP-02
- File: app.py:13
- Description: `SECRET_KEY` está no `app.py`. `services/notification_service.py:7-10` fixa host, usuário e senha de SMTP. `python-dotenv` está no `requirements.txt` e não é importado.
- Evidence: `app.config['SECRET_KEY'] = 'super-secret-key-123'`
- Impact: Chave de sessão e senha de e-mail no git. O serviço de e-mail nem é chamado pelas rotas, e o segredo já está exposto mesmo assim.
- Recommendation: `config/settings.py` lendo ambiente, com fallback de desenvolvimento só nesse arquivo. O serviço passa a receber a config, sem literal.
- Playbook: PB-02

### [HIGH] Rotas gordas no lugar de controller — AP-05
- File: routes/task_routes.py:86-154
- Description: `create_task` e `update_task` validam, consultam usuário e categoria, gravam e logam. O mesmo desenho está em `routes/user_routes.py` e em `routes/report_routes.py`. O CRUD de categoria mora no blueprint de relatório (`routes/report_routes.py:157-223`). `utils/helpers.py:57` já tem `process_task_data` e nenhuma rota chama.
- Evidence: `task = Task()`
- Impact: A regra de tarefa não roda sem HTTP. A pasta `routes/` parece camada e não é controller.
- Recommendation: Modo evolutivo. Extrair controllers e deixar o Blueprint com o decorator e a chamada. Models SQLAlchemy permanecem.
- Playbook: PB-04

### [HIGH] Schema criado no import — AP-06
- File: app.py:30-31
- Description: `db.create_all()` roda no import do módulo, fora de `__main__`. Importar `app` para o seed ou para um teste já cria `tasks.db` e as tabelas.
- Evidence: `db.create_all()`
- Impact: Efeito colateral global. O teste não controla o momento do schema.
- Recommendation: Mover `create_all` para o boot (`__main__` ou factory chamada pelo processo).
- Playbook: PB-06

### [HIGH] Token fictício, escalação de papel e rotas destrutivas abertas — AP-07
- File: routes/user_routes.py:210
- Description: O login devolve `fake-jwt-token-<id>`. Nenhuma rota lê `Authorization` nem o papel `admin` / `manager`. `DELETE /users/<id>`, `DELETE /tasks/<id>`, `DELETE /categories/<id>` e `GET /reports/*` são anônimos. O `role` do body em `routes/user_routes.py:52` e `122` vira papel privilegiado da conta sem checagem.
- Evidence: `'token': 'fake-jwt-token-' + str(user.id)`
- Impact: O token não protege nada; qualquer cliente anônimo cria conta `admin`, apaga usuários/tarefas/categorias e lê relatórios completos.
- Recommendation: Emitir token assinado real em `POST /login` (usando `SECRET_KEY`), proteger rotas destrutivas e administrativas (`DELETE /users/<id>`, `DELETE /tasks/<id>`, `DELETE /categories/<id>`, `GET /reports/*`) com `@require_auth`/`@require_roles` (`401`/`403`), e restringir atribuição de `role` privilegiado a administradores autenticados.
- Playbook: PB-12

### [MEDIUM] N+1 na listagem de tarefas, usuários e no relatório — AP-08
- File: routes/task_routes.py:42-52
- Description: Para cada tarefa, a listagem busca o usuário e a categoria com `query.get`, embora `Task.user` e `Task.category` já existam. `GET /users` acessa `len(u.tasks)` no laço (`routes/user_routes.py:15-24`). `GET /categories` conta tarefas com uma query por categoria (`routes/report_routes.py:163`). O resumo percorre usuários e, para cada um, carrega as tarefas (`routes/report_routes.py:53-61`).
- Evidence: `user = User.query.get(t.user_id)`
- Impact: Listar tarefas dispara 1 + 2N queries e listar usuários dispara 1 + N queries. O relatório repete o padrão por usuário e por categoria.
- Recommendation: `joinedload` nas relações já mapeadas (`Task.user`, `Task.category`, `User.tasks`) e contagem agrupada para categoria.
- Playbook: PB-05

### [MEDIUM] Atraso e validação reescritos em quatro lugares — AP-09
- File: routes/task_routes.py:30-39
- Description: A regra de overdue está copiada na listagem, no detalhe (`routes/task_routes.py:71-80`), nas tarefas do usuário (`routes/user_routes.py:171-180`) e no relatório (`routes/report_routes.py:34-37`). `Task.is_overdue` (`models/task.py:50-60`) já existe e não é chamada. Status válidos e tamanho de título também estão repetidos entre criar, atualizar e `utils/helpers.py`.
- Evidence: `if t.due_date < datetime.utcnow():`
- Impact: Corrigir atraso ou status exige achar todas as cópias. O model e o helper já eram a cópia certa.
- Recommendation: A rota chama `task.is_overdue()` e o validador único. As outras cópias saem.
- Playbook: PB-10

### [MEDIUM] `datetime.utcnow` e `Query.get` obsoletos — AP-10
- File: models/user.py:14
- Description: `datetime.utcnow` está em `models/user.py:14`, `models/task.py:15-16`, `models/task.py:52`, `models/category.py:11`, `routes/task_routes.py:31`, `72`, `215`, `285`, `routes/user_routes.py:172`, `routes/report_routes.py:35`, `45`, `71`, `133`, `services/notification_service.py:35`, `utils/helpers.py:38` e `seed.py:66`. `Model.query.get` está em `routes/task_routes.py:42`, `51`, `67`, `117`, `122`, `158`, `188`, `195`, `227`, `routes/user_routes.py:29`, `94`, `136`, `155` e `routes/report_routes.py:105`, `192`, `213`.
- Evidence: `created_at = db.Column(db.DateTime, default=datetime.utcnow)`
- Impact: Python 3.12 avisa em `utcnow`. Flask-SQLAlchemy 3 trata `Query.get` como API legada; o substituto é `session.get`.
- Recommendation: `datetime.now(timezone.utc)`, normalizando valor naive lido do SQLite na comparação. `db.session.get(Modelo, id)` no lugar de `.query.get`. Não reescrever os demais `.query.filter` nesta passagem.
- Playbook: PB-08

### [MEDIUM] `except` nu e erro genérico copiado — AP-11
- File: routes/task_routes.py:62
- Description: `get_tasks` usa `except:` vazio. Vários handlers repetem `except` com rollback e uma mensagem fixa (`routes/task_routes.py:236`, `routes/user_routes.py:149`, `routes/report_routes.py:186`). Não há `@app.errorhandler`.
- Evidence: `except:`
- Impact: A listagem engole até erro de programação. O contrato de 500 muda de frase conforme a rota.
- Recommendation: Um handler com a chave `error`, que é a que estas rotas já usam. Validação conhecida continua retornando 400 na função.
- Playbook: PB-09

### [LOW] Import morto e dependência declarada sem uso — AP-12
- File: app.py:7
- Description: `os`, `sys` e `json` entram em `app.py` e não são usados. `routes/task_routes.py:7` importa `json`, `os`, `sys` e `time`. `marshmallow`, `requests` e `python-dotenv` estão no `requirements.txt:4-6` e não aparecem em import de aplicação. `format_date` e `calculate_percentage` são importados em `routes/report_routes.py:7` e não são chamados.
- Evidence: `import os, sys, json, datetime`
- Impact: O manifesto mente sobre o que a API precisa. A leitura do entry point sugere código que não existe.
- Recommendation: Remover import morto nos arquivos tocados. Dependência ociosa sai do `requirements.txt` só se nenhum playbook passar a usá-la; `python-dotenv` permanece se PB-02 carregar `.env`.
- Playbook: PB-11

### [LOW] Limite de senha escrito de novo, ao lado da constante — AP-12
- File: routes/user_routes.py:64
- Description: `utils/helpers.py:114` define `MIN_PASSWORD_LENGTH = 4`. A rota compara com o literal `4` no criar e no atualizar (`routes/user_routes.py:115`).
- Evidence: `if len(password) < 4:`
- Impact: Subir o mínimo no helper não muda a API.
- Recommendation: Usar a constante que já existe, no arquivo que PB-04 for extrair.
- Playbook: PB-11

## Deprecated APIs

- `datetime.utcnow` em `models/user.py:14` e nas linhas listadas no finding AP-10 → `datetime.now(timezone.utc)`
- `Model.query.get` em `routes/task_routes.py:67` e nas linhas listadas no finding AP-10 → `db.session.get(Modelo, id)`
- `hashlib.md5` em `models/user.py:29` → `werkzeug.security.generate_password_hash` (finding AP-04; a senha do seed continua válida pelo caminho legado de PB-07)

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
