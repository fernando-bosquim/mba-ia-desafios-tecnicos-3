# ARCHITECTURE AUDIT REPORT

- Project: task-manager-api
- Stack: Python + Flask 3.0.0
- Files: 15 analyzed | 1158 lines
- Architecture: Camadas parciais
- DB: SQLite (`sqlite:///tasks.db` via SQLAlchemy) | tables: tasks, users, categories

## Summary

CRITICAL: 4 | HIGH: 7 | MEDIUM: 8 | LOW: 3

## Findings

### [CRITICAL] Hash de senha com MD5 e exposição do campo password em JSON — AP-04
- File: models/user.py:29
- Description: `User.set_password` (linha 29) e `User.check_password` (linha 32) aplicam `hashlib.md5` sem salt para armazenar e validar senhas. Além disso, `User.to_dict` (linha 21) serializa o campo `password`, vazando o digest nas respostas de `routes/user_routes.py` (linhas 33, 85, 129 e 209).
- Evidence: `self.password = hashlib.md5(pwd.encode()).hexdigest()`
- Impact: Qualquer cliente da API recebe o hash MD5 de senhas no JSON e o vazamento do banco permite quebra trivial por rainbow tables ou força bruta.
- Recommendation: Substituir MD5 por `werkzeug.security.generate_password_hash` e `check_password_hash`, e remover o campo `password` de `User.to_dict()`.
- Playbook: PB-07

### [CRITICAL] SECRET_KEY hardcoded no entrypoint — AP-02
- File: app.py:13
- Description: A chave secreta da aplicação Flask (`SECRET_KEY`) é atribuída como literal diretamente no código-fonte de `app.py`, junto à URI do banco (linha 11).
- Evidence: `app.config['SECRET_KEY'] = 'super-secret-key-123'`
- Impact: Segredo versionado no repositório compromete assinatura de sessões e tokens da aplicação.
- Recommendation: Mover `SECRET_KEY` e demais configurações sensíveis para um módulo `config.py` lido de variáveis de ambiente, documentando-as em `.env.example` com fallback apenas para desenvolvimento local.
- Playbook: PB-02

### [CRITICAL] Credenciais SMTP hardcoded em NotificationService — AP-02
- File: services/notification_service.py:10
- Description: `NotificationService.__init__` define credenciais de autenticação SMTP (`email_user` na linha 9 e `email_password` na linha 10) como literais no código-fonte.
- Evidence: `self.email_password = 'senha123'`
- Impact: Credenciais de e-mail ficam expostas no código versionado e acopladas à implementação do serviço.
- Recommendation: Ler host, porta, usuário e senha SMTP do módulo de configuração via variáveis de ambiente, sem literais sensíveis no código.
- Playbook: PB-02

### [CRITICAL] Token de autenticação fictício e previsível retornado no login — AP-02
- File: routes/user_routes.py:210
- Description: O endpoint `POST /login` devolve uma string estática previsível (`'fake-jwt-token-' + str(user.id)`) como token de autenticação, sem assinatura criptográfica nem validação posterior.
- Evidence: `'token': 'fake-jwt-token-' + str(user.id)`
- Impact: Qualquer cliente pode forjar ou prever tokens de outros usuários, criando falsa sensação de autenticação.
- Recommendation: Substituir o token fictício por token assinado com `SECRET_KEY` (ex.: `itsdangerous` ou HMAC-SHA256 com expiração) e validá-lo nas rotas protegidas.
- Playbook: PB-02

### [HIGH] Gestão de usuários permite escalação de privilégio e exclusão em cascata sem autenticação — AP-07
- File: routes/user_routes.py:134-151
- Description: `DELETE /users/<int:user_id>` remove o usuário e todas as suas tarefas sem qualquer checagem de autenticação ou autorização. Além disso, `POST /users` (linhas 52 e 78) e `PUT /users/<int:user_id>` (linhas 119-125) aceitam `role` (`admin`, `manager`) e `active` diretamente do corpo da requisição sem validação de permissão.
- Evidence: `@user_bp.route('/users/<int:user_id>', methods=['DELETE'])`
- Impact: Qualquer cliente anônimo pode criar contas administrativas, escalar privilégios de usuários existentes ou apagar usuários e tarefas em cascata.
- Recommendation: Aplicar middleware/decorator de autenticação e autorização administrativa (`PB-12`) nas operações privilegiadas de usuários e restringir alteração de `role`/`active` a administradores autenticados.
- Playbook: PB-12

### [HIGH] Relatórios administrativos globais e exclusão de categorias sem autenticação ou autorização — AP-07
- File: routes/report_routes.py:12-101
- Description: `GET /reports/summary` (linhas 12-101) e `GET /reports/user/<int:user_id>` (linhas 103-155) expõem métricas globais e produtividade individual de todos os usuários sem autenticação. No mesmo arquivo, `DELETE /categories/<int:cat_id>` (linhas 211-223) apaga categorias sem verificação de credencial ou papel.
- Evidence: `@report_bp.route('/reports/summary', methods=['GET'])`
- Impact: Dados operacionais consolidados de usuários e tarefas ficam abertos a acesso anônimo e categorias podem ser removidas por qualquer cliente.
- Recommendation: Proteger os endpoints de relatórios administrativos e a remoção de categorias com verificação de token assinado e papel autorizado (`401` sem credencial, `403` sem permissão).
- Playbook: PB-12

### [HIGH] Exclusão destrutiva de tarefas sem autenticação ou autorização — AP-07
- File: routes/task_routes.py:225-238
- Description: A rota `DELETE /tasks/<int:task_id>` apaga qualquer tarefa diretamente do banco de dados sem validar sessão, token assinado ou permissão do chamador.
- Evidence: `@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])`
- Impact: Qualquer cliente anônimo pode destruir registros de tarefas de qualquer usuário.
- Recommendation: Exigir autenticação e autorização via decorator (`PB-12`) em `DELETE /tasks/<int:task_id>`, retornando `401` sem credencial válida e `403` sem permissão.
- Playbook: PB-12

### [HIGH] Rotas gordas de tarefas concentram validação, regra de negócio e ORM — AP-05
- File: routes/task_routes.py:11-299
- Description: Todas as funções do blueprint `task_bp` (`get_tasks`, `get_task`, `create_task`, `update_task`, `delete_task`, `search_tasks`, `task_stats`) acumulam parsing HTTP, validação de entrada, cálculo de atraso, consultas/escritas diretas no SQLAlchemy e montagem de respostas.
- Evidence: `db.session.add(task)`
- Impact: As regras de domínio de tarefas não podem ser testadas ou reutilizadas sem o contexto HTTP do Flask, e qualquer mudança atravessa funções extensas na rota.
- Recommendation: Extrair a orquestração e regras de negócio para um `TaskController` (e camada de acesso/model), mantendo `routes/task_routes.py` restrito ao roteamento HTTP.
- Playbook: PB-04

### [HIGH] Rotas gordas de usuários concentram validação, regra de negócio e ORM — AP-05
- File: routes/user_routes.py:10-211
- Description: As rotas de `user_bp` (`get_users`, `get_user`, `create_user`, `update_user`, `delete_user`, `get_user_tasks`, `login`) executam validação de e-mail/senha/role, exclusão manual em cascata de tarefas, autenticação e transações ORM diretamente nas funções de rota.
- Evidence: `tasks = Task.query.filter_by(user_id=user_id).all()`
- Impact: Acopla regras de usuários e autenticação à camada HTTP, dificultando testes unitários e manutenção isolada.
- Recommendation: Mover a lógica de negócio e coordenação de persistência para um `UserController`, deixando `routes/user_routes.py` apenas como adaptador HTTP fino.
- Playbook: PB-04

### [HIGH] Blueprint de relatórios mistura regras de negócio, ORM e CRUD completo de categorias — AP-05
- File: routes/report_routes.py:12-223
- Description: `report_routes.py` concentra consultas ORM e agregações de relatórios (linhas 12-155) e ainda abriga todo o CRUD HTTP/ORM da entidade `Category` (`/categories`, linhas 157-223) dentro do mesmo blueprint `report_bp`.
- Evidence: `@report_bp.route('/categories', methods=['GET'])`
- Impact: Viola o princípio da responsabilidade única, mistura domínios distintos (relatórios e categorias) e acopla agregações pesadas diretamente às rotas.
- Recommendation: Separar categorias em seu próprio par rota/controller (`category_routes.py` e `category_controller.py`) e extrair a montagem de relatórios para `report_controller.py`.
- Playbook: PB-04

### [HIGH] Inicialização do banco executada no import do módulo principal — AP-06
- File: app.py:30-31
- Description: `db.create_all()` é executado no escopo de módulo de `app.py` (fora de uma app factory ou função de boot), disparando efeito colateral de banco toda vez que `app` é importado (como ocorre em `seed.py:2`).
- Evidence: `with app.app_context():`
- Impact: Testes e scripts que importam o módulo criam ou alteram o arquivo SQLite implicitamente, vazando estado global entre execuções.
- Recommendation: Encapsular a criação da aplicação em uma factory (`create_app`) e executar `db.create_all()` apenas na inicialização controlada do boot ou CLI.
- Playbook: PB-06

### [MEDIUM] Consultas N+1 em laço na listagem de tarefas — AP-08
- File: routes/task_routes.py:42
- Description: Dentro do laço `for t in tasks:` em `get_tasks` (linhas 16-59), o código executa `User.query.get(t.user_id)` (linha 42) e `Category.query.get(t.category_id)` (linha 51) para cada tarefa retornada.
- Evidence: `user = User.query.get(t.user_id)`
- Impact: O número de consultas SQL cresce linearmente (`1 + 2N`) com a quantidade de tarefas, degradando a latência do endpoint `GET /tasks`.
- Recommendation: Usar carregamento antecipado (`joinedload(Task.user)`, `joinedload(Task.category)`) em uma única consulta SQLAlchemy.
- Playbook: PB-05

### [MEDIUM] Acesso lazy N+1 à relação tasks na listagem de usuários — AP-08
- File: routes/user_routes.py:22
- Description: Dentro do laço `for u in users:` em `get_users` (linhas 14-24), `len(u.tasks)` dispara o carregamento lazy da coleção de tarefas para cada usuário.
- Evidence: `'task_count': len(u.tasks)`
- Impact: Executa `1 + N` consultas ao banco e carrega todas as linhas de `Task` em memória apenas para contar quantas tarefas cada usuário possui.
- Recommendation: Substituir o acesso lazy no laço por uma única consulta agregada com `OUTER JOIN` e `func.count(Task.id)` agrupada por `User.id`.
- Playbook: PB-05

### [MEDIUM] Consultas N+1 em laços nos relatórios e na listagem de categorias — AP-08
- File: routes/report_routes.py:56
- Description: `summary_report` executa `Task.query.filter_by(user_id=u.id).all()` dentro do laço `for u in users:` (linha 56), e `get_categories` executa `Task.query.filter_by(category_id=c.id).count()` dentro do laço `for c in categories:` (linha 163).
- Evidence: `user_tasks = Task.query.filter_by(user_id=u.id).all()`
- Impact: Gera `1 + N` consultas extras por relatório e por listagem de categorias, além de múltiplos `.count()` individuais por status e prioridade (linhas 19-28).
- Recommendation: Consolidar as contagens por usuário, categoria, status e prioridade usando consultas agregadas (`GROUP BY` / `func.count`) ou agregação única em memória.
- Playbook: PB-05

### [MEDIUM] Regra de cálculo de atraso (overdue) duplicada em seis endpoints ignorando Task.is_overdue() — AP-09
- File: routes/task_routes.py:30-39
- Description: A verificação de tarefa atrasada (`due_date < datetime.utcnow()` e `status not in ('done', 'cancelled')`) é copiada em `routes/task_routes.py` (linhas 30-39, 71-80 e 283-287), `routes/user_routes.py` (linhas 171-180) e `routes/report_routes.py` (linhas 33-37 e 132-135), ignorando o método `Task.is_overdue()` já existente em `models/task.py:50-60`.
- Evidence: `if t.due_date < datetime.utcnow():`
- Impact: Qualquer alteração na definição de atraso exige edição em sete locais distintos, com alto risco de divergência entre endpoints.
- Recommendation: Centralizar a regra em `Task.is_overdue()` e reutilizá-la em todos os controllers e relatórios.
- Playbook: PB-10

### [MEDIUM] Validação de tarefas e usuários duplicada entre rotas ignorando helpers e métodos de model — AP-09
- File: routes/task_routes.py:92-145
- Description: `create_task` (linhas 92-145) e `update_task` (linhas 166-214) duplicam validação de título, status, prioridade, data e tags, ignorando `utils/helpers.py:57-108` (`process_task_data`) e `models/task.py:38-48`. De forma análoga, `create_user` (`routes/user_routes.py:61-72`) e `update_user` (linhas 105-122) duplicam regex de e-mail, tamanho mínimo de senha e roles válidos (ignorando `validate_email` em `utils/helpers.py:19-23`), e `completion_rate` é reimplementado em `routes/report_routes.py:67, 151` e `routes/task_routes.py:296` ignorando `calculate_percentage` (`utils/helpers.py:14-17`).
- Evidence: `if status not in ['pending', 'in_progress', 'done', 'cancelled']:`
- Impact: Regras de validação e cálculo ficam espalhadas e sujeitas a inconsistências (ex.: `create_task` exige tamanho de título sem `strip()`, diferente de `process_task_data`).
- Recommendation: Unificar validações e cálculos em validadores/helpers compartilhados e chamá-los a partir dos controllers.
- Playbook: PB-10

### [MEDIUM] Uso da API legada .query.get() do SQLAlchemy 1.x — AP-10
- File: routes/task_routes.py:67
- Description: O projeto utiliza `Modelo.query.get(id)` (API legada de `Query` no SQLAlchemy 2 / Flask-SQLAlchemy 3) em 16 pontos: `routes/task_routes.py` (linhas 42, 51, 67, 117, 122, 158, 188, 195, 227), `routes/user_routes.py` (linhas 29, 94, 136, 155) e `routes/report_routes.py` (linhas 105, 192, 213).
- Evidence: `task = Task.query.get(task_id)`
- Impact: Emite `LegacyAPIWarning` no SQLAlchemy 2.x e pode quebrar em futuras atualizações do ORM.
- Recommendation: Substituir todas as chamadas `.query.get(id)` por `db.session.get(Modelo, id)`.
- Playbook: PB-08

### [MEDIUM] Uso de datetime.utcnow() deprecado no Python 3.12 — AP-10
- File: models/task.py:15
- Description: `datetime.utcnow` é usado em 22 pontos do projeto: `models/category.py:11`, `models/task.py:15, 16, 52`, `models/user.py:14`, `routes/task_routes.py:31, 72, 215, 285`, `routes/user_routes.py:172`, `routes/report_routes.py:35, 42, 45, 71, 133`, `services/notification_service.py:35`, `utils/helpers.py:38` e `seed.py:66, 67, 69, 70, 74`.
- Evidence: `created_at = db.Column(db.DateTime, default=datetime.utcnow)`
- Impact: Deprecado no Python 3.12 por retornar objetos naive sem fuso horário e sujeito a remoção futura.
- Recommendation: Substituir `datetime.utcnow()` por `datetime.now(timezone.utc)` (com callable `lambda: datetime.now(timezone.utc)` nas colunas SQLAlchemy).
- Playbook: PB-08

### [MEDIUM] Tratamento de erro espalhado com bare except e ausência de handler centralizado — AP-11
- File: routes/task_routes.py:62
- Description: Não há `@app.errorhandler` centralizado; rotas e utilitários repetem blocos `try/except` com `except:` genérico engolindo exceções em `routes/task_routes.py` (linhas 62, 137, 151, 204, 221, 236), `routes/user_routes.py` (linhas 87, 130, 149), `routes/report_routes.py` (linhas 186, 207, 221) e `utils/helpers.py` (linhas 46, 49, 88). Além disso, `search_tasks` (`routes/task_routes.py:261, 264`) converte `int(priority)`/`int(user_id)` sem tratamento e `update_category` (`routes/report_routes.py:196-197`) não valida `data is None`, gerando erro 500 HTML em entradas inválidas.
- Evidence: `except:`
- Impact: Oculta causa real de falhas (incluindo `KeyboardInterrupt`/`SystemExit` em `except:` puro) e entrega respostas de erro inconsistentes entre rotas.
- Recommendation: Registrar handlers globais com `@app.errorhandler`, usar exceções específicas (ex.: `ValueError`, `SQLAlchemyError`) e validar parâmetros de query e corpo JSON antes do uso.
- Playbook: PB-09

### [LOW] Imports não usados e dependências ociosas em requirements.txt — AP-12
- File: requirements.txt:4-6
- Description: Os pacotes `marshmallow==3.20.1`, `requests==2.31.0` e `python-dotenv==1.0.0` estão declarados em `requirements.txt` sem nenhum import no código. Há também imports não utilizados em `app.py:7` (`os`, `sys`, `json`), `models/task.py:3` (`json`), `routes/task_routes.py:7` (`json`, `os`, `sys`, `time`), `routes/user_routes.py:6` (`hashlib`, `json`), `routes/report_routes.py:7-8` (`format_date`, `calculate_percentage`, `json`) e `utils/helpers.py:3-7` (`os`, `json`, `sys`, `math`, `hashlib`).
- Evidence: `marshmallow==3.20.1`
- Impact: Aumenta a superfície de dependências instaladas e dificulta a leitura do que cada módulo realmente consome.
- Recommendation: Remover imports mortos e manter em `requirements.txt` apenas dependências efetivamente usadas (ou adotar `python-dotenv` no módulo de configuração).
- Playbook: PB-11

### [LOW] Serviço de notificação, helpers e constantes mortos ou ignorados — AP-12
- File: utils/helpers.py:9-116
- Description: Todas as funções e constantes de `utils/helpers.py` (`format_date`, `calculate_percentage`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data` e constantes das linhas 110-116), a classe `NotificationService` (`services/notification_service.py:4-48`) e métodos de model (`Task.validate_status`, `Task.validate_priority`, `Task.is_overdue` em `models/task.py:38-60` e `User.is_admin` em `models/user.py:34-38`) nunca são chamados pela aplicação.
- Evidence: `VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']`
- Impact: Código morto gera confusão sobre qual implementação está ativa e favorece divergência quando números mágicos são repetidos nas rotas.
- Recommendation: Reutilizar os helpers, constantes e métodos de domínio nos controllers durante a refatoração e remover funções que permanecerem sem uso.
- Playbook: PB-11

### [LOW] Uso de print() no fluxo de produção e checagem frágil com type() == list — AP-12
- File: routes/task_routes.py:141
- Description: As rotas utilizam `type(...) == list` em vez de `isinstance(..., list)` em `routes/task_routes.py:141, 210` e `utils/helpers.py:103`, além de `print()` para logging no fluxo de produção em `routes/task_routes.py:149, 153, 219, 234`, `routes/user_routes.py:83, 89, 147` e `services/notification_service.py:21, 24`.
- Evidence: `if type(tags) == list:`
- Impact: `type() == list` não suporta subclasses e `print()` sem nível/estruturador polui stdout sem controle de severidade.
- Recommendation: Trocar `type(x) == list` por `isinstance(x, list)` e substituir `print()` por `logging` estruturado.
- Playbook: PB-11

## Deprecated APIs

- `datetime.utcnow` em `models/category.py:11` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `models/task.py:15` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `models/task.py:16` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `models/task.py:52` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `models/user.py:14` → `datetime.now(timezone.utc)`
- `hashlib.md5` em `models/user.py:29` → `werkzeug.security.generate_password_hash`
- `hashlib.md5` em `models/user.py:32` → `werkzeug.security.check_password_hash`
- `datetime.utcnow` em `routes/task_routes.py:31` → `datetime.now(timezone.utc)`
- `.query.get(` em `routes/task_routes.py:42` → `db.session.get(User, t.user_id)`
- `.query.get(` em `routes/task_routes.py:51` → `db.session.get(Category, t.category_id)`
- `.query.get(` em `routes/task_routes.py:67` → `db.session.get(Task, task_id)`
- `datetime.utcnow` em `routes/task_routes.py:72` → `datetime.now(timezone.utc)`
- `.query.get(` em `routes/task_routes.py:117` → `db.session.get(User, user_id)`
- `.query.get(` em `routes/task_routes.py:122` → `db.session.get(Category, category_id)`
- `.query.get(` em `routes/task_routes.py:158` → `db.session.get(Task, task_id)`
- `.query.get(` em `routes/task_routes.py:188` → `db.session.get(User, data['user_id'])`
- `.query.get(` em `routes/task_routes.py:195` → `db.session.get(Category, data['category_id'])`
- `datetime.utcnow` em `routes/task_routes.py:215` → `datetime.now(timezone.utc)`
- `.query.get(` em `routes/task_routes.py:227` → `db.session.get(Task, task_id)`
- `datetime.utcnow` em `routes/task_routes.py:285` → `datetime.now(timezone.utc)`
- `.query.get(` em `routes/user_routes.py:29` → `db.session.get(User, user_id)`
- `.query.get(` em `routes/user_routes.py:94` → `db.session.get(User, user_id)`
- `.query.get(` em `routes/user_routes.py:136` → `db.session.get(User, user_id)`
- `.query.get(` em `routes/user_routes.py:155` → `db.session.get(User, user_id)`
- `datetime.utcnow` em `routes/user_routes.py:172` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `routes/report_routes.py:35` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `routes/report_routes.py:42` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `routes/report_routes.py:45` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `routes/report_routes.py:71` → `datetime.now(timezone.utc)`
- `.query.get(` em `routes/report_routes.py:105` → `db.session.get(User, user_id)`
- `datetime.utcnow` em `routes/report_routes.py:133` → `datetime.now(timezone.utc)`
- `.query.get(` em `routes/report_routes.py:192` → `db.session.get(Category, cat_id)`
- `.query.get(` em `routes/report_routes.py:213` → `db.session.get(Category, cat_id)`
- `datetime.utcnow` em `services/notification_service.py:35` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `utils/helpers.py:38` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `seed.py:66` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `seed.py:67` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `seed.py:69` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `seed.py:70` → `datetime.now(timezone.utc)`
- `datetime.utcnow` em `seed.py:74` → `datetime.now(timezone.utc)`

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
