# Refatoração arquitetural automatizada

A skill `refactor-arch` audita um backend legado e refatora o código para MVC. Os arquivos ficam em `.cursor/skills/refactor-arch/`, na convenção de Agent Skill do Cursor: `SKILL.md` com frontmatter e os Markdown de referência ao lado.

O agente do Cursor executa as três fases. O conhecimento de domínio está nesses Markdown. O agente aplica esse conhecimento no código.

## Análise manual

A leitura dos três projetos foi feita antes da skill. A severidade segue a escala do curso. Cada item está no relatório da Fase 2.

### code-smells-project (Python, Flask 3.1.1)

API de e-commerce. Quatro arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), 780 linhas, SQLite em `loja.db`.

| Sev. | Onde | Problema | Por que importa |
|---|---|---|---|
| CRITICAL | `models.py:28` (e as demais queries montadas no mesmo arquivo) | SQL por concatenação de id, nome, e-mail, senha e filtro | Um campo de busca ou de login muda o comando executado no banco |
| CRITICAL | `app.py:7` e `controllers.py:289` | `SECRET_KEY` no fonte e de novo no JSON de `/health` | O segredo está no git e sai para qualquer cliente do health |
| CRITICAL | `models.py:1-314` | Um módulo faz SQL e a regra de produto, usuário, pedido e relatório | Testar um domínio exige carregar os outros quatro |
| HIGH | `controllers.py:188-250` | Estoque, status e "envio" de e-mail/SMS/push dentro da função da rota | A regra fica dentro do `request` |
| MEDIUM | `models.py:186-193` | Para cada pedido, uma query de itens; para cada item, uma query de produto | O custo cresce com pedidos × itens, e a query ainda é concatenada |
| MEDIUM | `controllers.py:30-50` e `74-90` | A mesma validação de produto está escrita duas vezes, e a de categoria só no criar | A atualização já divergiu da criação |
| LOW | `models.py:257-262` | Limiares `10000`, `5000`, `1000` e taxas `0.1`, `0.05`, `0.02` soltos | Os literais são a regra de desconto |
| LOW | `controllers.py:8` | `print` com concatenação no fluxo feliz | Ruído na saída |

### ecommerce-api-legacy (JavaScript, Express ^4.18.2)

LMS com checkout. Três arquivos em `src/`, 180 linhas, SQLite em memória.

| Sev. | Onde | Problema | Por que importa |
|---|---|---|---|
| CRITICAL | `src/AppManager.js:3-139` | A classe abre o banco, cria as tabelas e implementa as três rotas | O arquivo é o sistema inteiro |
| CRITICAL | `src/utils.js:3-5` e `src/AppManager.js:45` | Senha, chave `pk_live` e SMTP no fonte; o checkout escreve o cartão no log | Credencial de gateway no git e número do cartão no stdout |
| HIGH | `src/AppManager.js:28-77` | Pagamento, matrícula e usuário novo dentro do callback da rota | A regra do primeiro dígito do cartão está no callback HTTP |
| MEDIUM | `src/AppManager.js:89-123` | Query de matrícula, usuário e pagamento dentro de laços, com contador manual de callback | A resposta pode sair duas vezes ou não sair |
| MEDIUM | `src/AppManager.js:1` | `sqlite3.verbose()` e acesso só por callback | API antiga do driver, com trace ligado no boot |
| MEDIUM | `src/AppManager.js:131-136` | Delete de usuário deixa matrícula e pagamento no banco | A resposta avisa a matrícula e o pagamento que ficam no banco |
| LOW | `src/AppManager.js:29-33` | Variáveis `u`, `e`, `p`, `cid`, `cc` | A regra de cobrança fica ilegível |
| LOW | `src/AppManager.js:68` | Fallback `"123456"` quando o body não traz senha | Conta nova nasce com segredo conhecido |

### task-manager-api (Python, Flask 3.0.0, Flask-SQLAlchemy 3.1.1)

API de tarefas. Há `models/`, `routes/`, `services/` e `utils/`. Doze arquivos de aplicação, 1155 linhas, SQLite em `tasks.db`. A rota ainda valida, consulta e decide.

| Sev. | Onde | Problema | Por que importa |
|---|---|---|---|
| CRITICAL | `models/user.py:29` e `models/user.py:21` | Senha em MD5 sem sal, e o hash vai no `to_dict` e no login | `GET /users/<id>` e `POST /login` entregam o hash; MD5 de senha curta cai em tabela pré-calculada |
| HIGH | `app.py:13` e `services/notification_service.py:10` | `SECRET_KEY` e senha de SMTP no fonte. `python-dotenv` está no manifesto e não é usado | Segredo versionado, inclusive num serviço que nenhuma rota chama |
| HIGH | `routes/task_routes.py:86-154` | Criar e atualizar tarefa concentram validação, ORM e log. Categoria mora no blueprint de relatório | A regra está no HTTP. `process_task_data` existe e nenhuma rota o chama |
| MEDIUM | `routes/task_routes.py:42-52` | `User.query.get` e `Category.query.get` dentro do laço da listagem | 1 + 2N queries. As relações estão em `Task.user` e `Task.category` |
| MEDIUM | `models/user.py:14` e `routes/task_routes.py:67` | `datetime.utcnow` (deprecado no Python 3.12) e `Query.get` (API legada do SQLAlchemy 2) | Aviso de runtime no `utcnow`. O Flask-SQLAlchemy 3 trata `Query.get` como API antiga |
| MEDIUM | `routes/task_routes.py:30-39` | A regra de atraso está copiada na listagem, no detalhe, no usuário e no relatório. `Task.is_overdue` não é chamado | Uma correção precisa achar as quatro cópias |
| LOW | `app.py:7` | `os`, `sys` e `json` importados e não usados. `marshmallow` e `requests` declarados sem import | O entry point e o manifesto descrevem código que não existe |
| LOW | `routes/user_routes.py:64` | Comparação com `4` ao lado de `MIN_PASSWORD_LENGTH = 4` em `utils/helpers.py:114` | Mudar a constante não muda a API |

## Construção da skill

### Onde ela mora

| Caminho | Papel |
|---|---|
| `.cursor/skills/refactor-arch/` | Skill do workspace. O Cursor carrega esta pasta com o repositório aberto na raiz |
| `code-smells-project/.cursor/skills/refactor-arch/` | Cópia da entrega, para quem abre só o projeto 1 |
| `ecommerce-api-legacy/.cursor/skills/refactor-arch/` | Cópia da entrega, projeto 2 |
| `task-manager-api/.cursor/skills/refactor-arch/` | Cópia da entrega, projeto 3 |

As quatro pastas têm os mesmos seis arquivos. Com `disable-model-invocation: true`, a skill entra quando é chamada pelo nome `refactor-arch`.

### Arquivos

| Arquivo | Conteúdo |
|---|---|
| `SKILL.md` | Fases, gates e o caminho do relatório |
| `analise-de-projeto.md` | Linguagem, manifest, framework, banco, entry point e classe de arquitetura |
| `catalogo-anti-patterns.md` | Doze anti-patterns, AP-01 a AP-12, com sinal, falso positivo e severidade |
| `template-relatorio.md` | Formato do Markdown da Fase 2 e os banners de console |
| `guidelines-mvc.md` | Camadas, três modos de migração, contrato HTTP, config e validação |
| `playbook-refatoracao.md` | Doze transformações, PB-01 a PB-12, com antes e depois |

O `SKILL.md` manda ler o material da fase atual. A auditoria usa o catálogo e o template. Guidelines e playbook entram depois do sim.

### Catálogo

A escala do curso define a severidade. SQL concatenada, segredo e God module são CRITICAL. Rota gorda e estado global são HIGH. N+1, duplicação, API obsoleta e erro engolido são MEDIUM. Nome, número mágico e import morto são LOW.

O catálogo fixa dois critérios neste código:

- God module é um arquivo que mistura SQL, regra e mais de uma entidade. `models.py` do projeto 1 faz isso num módulo de funções.
- Projeto com `models/` e `routes/` segue o modo evolutivo na Fase 3. Entram `controllers/` e `config/`. A rota fica fina. O ORM permanece.

AP-10 é a passagem obrigatória de API obsoleta. Cada item tem substituto. A lista traz `datetime.utcnow`, `Query.get`, MD5 de senha, `sqlite3.verbose()`, `body-parser`, `app.del`, `res.sendfile`, `new Buffer` e `before_first_request`. No projeto 3 ela acha `utcnow` e `Query.get`. No projeto 2, `sqlite3.verbose()`. No projeto 1, o relatório registra a varredura vazia.

### Stack e relatório

A Fase 1 decide a stack pelo manifest e pelos imports. Cobre Python, JavaScript, Go, Java, PHP, Ruby e C#. O catálogo descreve o sinal no texto da query e na borda HTTP. Depois mostra a forma Python e a forma JavaScript. O playbook repete o par quando a sintaxe muda (`?` no `sqlite3` e no driver do Node). A árvore alvo tem uma variante Flask e uma Express. O modo de migração olha as pastas que já existem.

O relatório padrão sai como `reports/audit-<pasta>.md`. Os nomes `audit-project-1.md`, `audit-project-2.md` e `audit-project-3.md` foram informados na execução deste desafio.

### Contrato HTTP

A Fase 3 inventaria método, caminho, status e chaves antes da primeira edição. Rotas públicas de negócio não apontadas por `AP-07` seguem aceitando chamadas sem credencial. Campo que vaza senha, hash, segredo, cartão ou token fictício sai da resposta. SQL enviado pelo cliente deixa de executar (`400`).

Para todas as rotas destrutivas, administrativas ou de escalação de privilégio apontadas por `AP-07` na Fase 2, `PB-12` exige proteção na Fase 3 como mudança intencional de segurança:

- **Projetos com `/login` e papéis (`code-smells-project` e `task-manager-api`):** `POST /login` emite `token` assinado com `SECRET_KEY` (`itsdangerous.URLSafeTimedSerializer`, já incluso no Flask). Rotas administrativas e destrutivas exigem `Authorization: Bearer <token>` e devolvem `401` (sem token válido), `403` (sem permissão) e `200` (autorizada, ou `400` para recusa de SQL arbitrário em `/admin/query`). Atribuição anônima de `role` privilegiado também é bloqueada (`403`).
- **Projeto sem `/login` (`ecommerce-api-legacy`):** `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Key` (ou `Authorization: Bearer <key>`) comparado em tempo constante (`crypto.timingSafeEqual`) com `ADMIN_API_KEY` do módulo de `config` (`401` ausente, `403` inválida, `200` autorizada).

Monolito e task manager usam a mesma skill. O monolito recebe pasta nova. O task manager recebe controllers, `config/`, `middlewares/` e extração de `categories` sobre o que já existe. Os três sobem depois da refatoração.

### Desafios

- `check_same_thread=False` entra em AP-06 como estado global. O playbook usa `flask.g` para cada request do Flask ter a própria conexão.
- Hash novo quebra o seed se o login só comparar digest. PB-07 mantém o caminho legado com upgrade transparente no login.
- `Query.get` é API obsoleta (MEDIUM). N+1 é outro achado (MEDIUM), mesmo quando os dois aparecem na mesma linha. A correção trata os dois em separado.
- Rotas destrutivas/administrativas apontadas por `AP-07` sem mecanismo prévio de autenticação: `PB-12` define duas estratégias sem adicionar dependências externas (token assinado via `itsdangerous` quando há `/login`, ou `ADMIN_API_KEY` via config quando não há login), garantindo `401`/`403` sem bloquear rotas públicas de negócio.
- O serviço de e-mail que fazia `print` ou log pode usar logging estruturado sem depender de servidor SMTP externo.

## Resultados

Fases 1, 2 e 3 executadas. A Fase 3 só começou depois da confirmação. Os três processos subiram e os endpoints originais responderam.

### Fase 1

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        API de e-commerce (produtos, usuários, pedidos)
Architecture:  Monolítica — quatro arquivos, sem pacote de domínio
Source files:  4 files analyzed
DB:            SQLite (loja.db) | tables: produtos, usuarios, pedidos, itens_pedido
Entry:         app.py:88 | 0.0.0.0:5000
================================
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6
Domain:        LMS com checkout (usuários, cursos, matrículas, pagamentos)
Architecture:  Monolítica — AppManager abre o banco e registra as rotas
Source files:  3 files analyzed
DB:            SQLite em memória | tables: users, courses, enrollments, payments, audit_logs
Entry:         src/app.js:12 | localhost:3000
================================
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1 (sem uso), requests 2.31.0 (sem uso), python-dotenv 1.0.0 (sem uso)
Domain:        API de tarefas (tasks, users, categories)
Architecture:  Camadas parciais — models, routes, services e utils; a rota ainda concentra a regra
Source files:  12 files analyzed
DB:            SQLite (tasks.db) | tables: users, tasks, categories
Entry:         app.py:34 | 0.0.0.0:5000
================================
```

### Fase 2

| Projeto | Relatório | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---:|---:|---:|---:|---:|
| code-smells-project | `reports/audit-project-1.md` | 5 | 3 | 3 | 2 | 13 |
| ecommerce-api-legacy | `reports/audit-project-2.md` | 3 | 3 | 3 | 2 | 11 |
| task-manager-api | `reports/audit-project-3.md` | 2 | 3 | 4 | 2 | 11 |

Os oito itens de cada análise manual estão nos relatórios. A Fase 2 acrescenta o que a leitura inicial não listou na tabela (SQL livre em `/admin/query`, senha em texto puro, conexão global, reset anônimo, hash caseiro, cache global, token fictício, `create_all` no import, `except` nu).

API obsoleta: nenhuma no projeto 1; `sqlite3.verbose()` no projeto 2; `datetime.utcnow`, `Query.get` e MD5 no projeto 3.

### Estrutura, antes e depois da Fase 3

| Projeto | Antes | Depois |
|---|---|---|
| code-smells-project | `app.py`, `controllers.py`, `models.py`, `database.py` | `app.py` fino, `config/`, `models/` (sem regra de desconto nem `reset` em `pedido_model`), `controllers/`, `views/routes.py`, `middlewares/auth.py` e `middlewares/error_handler.py` |
| ecommerce-api-legacy | `src/app.js`, `AppManager.js`, `utils.js` | `src/app.js` fino, `src/config/`, `src/models/` (`db.js` + repositórios por entidade: `course`, `user`, `enrollment`, `payment`, `auditLog`), `src/controllers/`, `src/views/routes.js`, `src/middlewares/authMiddleware.js` e `errorHandler.js` |
| task-manager-api | `models/`, `routes/` gordas (categorias dentro de reports), `services/`, `utils/` | `models/`, `services/` e `utils/` permanecem. Entraram `controllers/` (incluindo `category_controller.py`), `routes/category_routes.py`, `config/`, `middlewares/auth.py` e `middlewares/error_handler.py`. Rotas finas; ORM preservado |

### Checklist de validação

#### code-smells-project

##### Fase 1 — Análise
- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

##### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados
- [x] Detecção de APIs deprecated incluída (varredura vazia, declarada)
- [x] Skill pausa e pede confirmação antes da Fase 3

##### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

#### ecommerce-api-legacy

##### Fase 1 — Análise
- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

##### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados
- [x] Detecção de APIs deprecated incluída (`sqlite3.verbose()`)
- [x] Skill pausa e pede confirmação antes da Fase 3

##### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

#### task-manager-api

##### Fase 1 — Análise
- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

##### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados
- [x] Detecção de APIs deprecated incluída (`utcnow`, `Query.get`, MD5)
- [x] Skill pausa e pede confirmação antes da Fase 3

##### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

### Validação da Fase 3

Mudanças de contrato intencionais de segurança (registradas conforme `AP-01`, `AP-02`, `AP-04` e `AP-07`/`PB-12`):

- **Loja (`code-smells-project`):** `/health` não devolve mais `secret_key`, `db_path` nem `debug`. `GET /usuarios` e `GET /usuarios/<id>` não devolvem `senha`. `POST /login` emite `token` assinado com `SECRET_KEY`. `POST /admin/reset-db` e `POST /admin/query` exigem token de administrador (`401` anônimo, `403` cliente comum, `200` no reset para admin, e `400` `Query não permitida` para SQL do cliente mesmo autenticado como admin). `PUT /produtos/<id>` passa a validar categoria e tamanho do nome de forma idêntica ao `POST /produtos`.
- **LMS (`ecommerce-api-legacy`):** `POST /api/checkout` mantém sucesso (`200`), `"Pagamento recusado"` (`400`) e `"Bad Request"` (`400`), sem expor número do cartão nem chave de gateway no log. `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Key` (ou `Authorization: Bearer`) válido (`401` ausente, `403` inválido, `200` autorizado). `DELETE /api/users/:id` agora remove `payments` e `enrollments` em transação antes do usuário (retornando `404` se não existir), eliminando registros órfãos.
- **Tarefas (`task-manager-api`):** `POST /login` continua `200` com as senhas do seed (`1234`, `abcd`, `pass`), sem `password`, substituindo o token fictício por `token` assinado real. `GET /reports/summary` (`admin`/`manager`), `GET /reports/user/<id>` (próprio usuário ou `admin`/`manager`), `DELETE /categories/<id>` (`admin`/`manager`), `DELETE /tasks/<id>` (dono ou `admin`/`manager`) e `DELETE /users/<id>` (`admin`) respondem `401`/`403` quando não autorizados e `200` quando autorizados. `POST /users` e `PUT /users/<id>` bloqueiam atribuição de `role` privilegiado sem token de administrador (`403`).

Logs reais de boot e validação ponta a ponta (executados após as alterações finais):

#### 1. `code-smells-project` (`python app.py` — 31/31 verificações)

```text
==================================================
SERVIDOR INICIADO
Rodando em http://0.0.0.0:5000
==================================================
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000

GET  /health                              -> 200 (sem secret_key/db_path/debug)
GET  /produtos                            -> 200 (10 produtos do seed)
GET  /produtos/busca?preco_min=abc        -> 400 {"erro": "Parâmetro de preço inválido"}
PUT  /produtos/11 (categoria invalida)    -> 400 {"erro": "Categoria inválida..."}
GET  /usuarios                            -> 200 (sem campo senha)
POST /login (joao@email.com / 123456)     -> 200 (token Bearer cliente)
POST /login (admin@loja.com / admin123)   -> 200 (token Bearer admin)
POST /pedidos                             -> 201 {"dados": {"pedido_id": 1, "total": 179.8}}
GET  /relatorios/vendas                   -> 200
POST /admin/query (anonimo)               -> 401 {"erro": "Autenticação obrigatória"}
POST /admin/query (cliente)               -> 403 {"erro": "Acesso restrito a administradores"}
POST /admin/query (admin, DROP TABLE)     -> 400 {"erro": "Query não permitida"}
POST /admin/reset-db (anonimo)            -> 401 (GET /produtos permanece com 10 itens)
POST /admin/reset-db (cliente)            -> 403 {"erro": "Acesso restrito a administradores"}
POST /admin/reset-db (admin)              -> 200 {"mensagem": "Banco de dados resetado", "sucesso": true}
```

#### 2. `ecommerce-api-legacy` (`npm start` — 12/12 verificações)

```text
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js

Frankenstein LMS rodando na porta 3000...
Checkout aprovado: matrícula 2, status PAID
Pagamento recusado: usuário 3, curso 1

POST   /api/checkout (cartão 4111...)             -> 200 {"msg": "Sucesso", "enrollment_id": 2}
POST   /api/checkout (cartão 5111...)             -> 400 "Pagamento recusado"
POST   /api/checkout (campos ausentes)            -> 400 "Bad Request"
GET    /api/admin/financial-report (sem header)   -> 401 {"error": "Credencial administrativa obrigatória"}
GET    /api/admin/financial-report (chave errada) -> 403 {"error": "Credencial administrativa inválida"}
GET    /api/admin/financial-report (X-Admin-Key)  -> 200 (Clean Architecture 997, Docker 497)
DELETE /api/users/1 (sem header)                  -> 401 {"error": "Credencial administrativa obrigatória"}
DELETE /api/users/1 (chave errada)                -> 403 {"error": "Credencial administrativa inválida"}
DELETE /api/users/1 (X-Admin-Key)                 -> 200 {"msg": "Usuário e registros vinculados removidos com sucesso"}
GET    /api/admin/financial-report (pós-delete)   -> 200 (Clean Architecture revenue: 0, students: [] — zero órfãos)
DELETE /api/users/999 (X-Admin-Key)               -> 404 {"error": "Usuário não encontrado"}
```

#### 3. `task-manager-api` (`python -W default seed.py && python -W default app.py` — 45/45 verificações, zero `DeprecationWarning` e zero `LegacyAPIWarning`)

```text
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks

 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000

GET    /health                             -> 200
GET    /tasks                              -> 200 (10 tasks)
GET    /tasks/search?priority=abc          -> 400 {"error": "Filtro numérico inválido"}
GET    /users                              -> 200 (3 usuários, sem password)
GET    /categories                         -> 200 (4 categorias)
POST   /login (joao/maria/pedro do seed)   -> 200 (token assinado real, sem password)
POST   /users (anônimo com role=admin)     -> 403 {"error": "Apenas administradores podem atribuir este role"}
PUT    /users/4 (user comum role=admin)    -> 403 {"error": "Apenas administradores podem alterar role"}
GET    /reports/summary (anônimo / user)   -> 401 / 403
GET    /reports/summary (admin)            -> 200
GET    /reports/user/1 (anônimo / maria)   -> 401 / 403
GET    /reports/user/2 (maria próprio)     -> 200
DELETE /tasks/1 (anônimo / maria / joao)   -> 401 / 403 / 200
DELETE /categories/4 (anônimo / user / mgr)-> 401 / 403 / 200 (categoria nova)
DELETE /users/2 (anônimo / user / manager) -> 401 / 403 / 403
DELETE /users/4 (admin)                    -> 200 {"message": "Usuário deletado com sucesso"}
```

### O que a skill fez de diferente em cada stack

No Flask monolítico os findings graves são SQL, segredo no health e módulo único. No Express o grave é a classe que é o processo, SQL nos controllers, registros órfãos no delete, mais segredo e cartão no log; o SQL de negócio já usa `?`, então AP-01 não dispara à toa. No Flask com camadas a skill não finge God class: marca rota gorda, categorias acopladas em relatórios, MD5, token fictício, `create_all` no import e a API obsoleta do ORM. O mesmo catálogo, três desenhos — e nos três projetos `AP-07`/`PB-12` protege efetivamente as rotas destrutivas e administrativas.

## Como executar

### Pré-requisitos

- Cursor com este repositório aberto na raiz.
- Python 3 com `pip` para os dois projetos Flask.
- Node.js com `npm` para o projeto Express.
- Nenhum servidor nas portas 5000 e 3000 na hora da Fase 3. Os dois Flask usam 5000; rode um de cada vez.

### Comandos

No chat do Cursor, um projeto por vez:

```
Execute a skill refactor-arch no projeto code-smells-project.
Grave o relatório em reports/audit-project-1.md.
Comece pela Fase 1 e pare na confirmação da Fase 2.
```

```
Execute a skill refactor-arch no projeto ecommerce-api-legacy.
Grave o relatório em reports/audit-project-2.md.
Comece pela Fase 1 e pare na confirmação da Fase 2.
```

```
Execute a skill refactor-arch no projeto task-manager-api.
Grave o relatório em reports/audit-project-3.md.
Comece pela Fase 1 e pare na confirmação da Fase 2.
```

A skill só edita código de aplicação depois de uma resposta `s`, `sim`, `y` ou `yes` à pergunta da Fase 2. Os relatórios desta execução já estão em `reports/`.

Quem abrir só uma pasta de projeto encontra a mesma skill em `.cursor/skills/refactor-arch/` dentro dessa pasta.

### Como validar a refatoração

Depois da Fase 3, a própria skill sobe o processo e chama as rotas. Na mão:

```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
```

`GET http://localhost:5000/health` responde 200 (sem `secret_key`). `GET http://localhost:5000/produtos` devolve os 10 produtos do seed. `POST /admin/reset-db` e `POST /admin/query` respondem `401` sem token, `403` para cliente comum (`joao@email.com` / `123456`) e exigem o Bearer token de `admin@loja.com` / `admin123` obtido em `POST /login` (`/admin/query` ainda recusa SQL arbitrário com `400`).

```bash
cd ecommerce-api-legacy
npm install
npm start
```

Os exemplos de `api.http` funcionam na porta 3000: checkout com cartão `4111...` em `200`, cartão `5111...` em `400` (`Pagamento recusado`). `GET /api/admin/financial-report` e `DELETE /api/users/1` exigem `X-Admin-Key: dev-admin-key-change-me` (`401` sem chave, `403` chave inválida, `200` autorizado, sem deixar matrículas nem pagamentos órfãos).

```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py
```

`GET /health`, `GET /tasks`, `GET /categories` e `POST /login` (`joao@email.com` / `1234`) retornam `200`, sem `password` e com `token` assinado real. Use `Authorization: Bearer <token>` nas rotas protegidas (`/reports/summary`, `/reports/user/<id>`, `DELETE /tasks/<id>`, `DELETE /categories/<id>` e `DELETE /users/<id>`).
