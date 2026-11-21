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
| MEDIUM | `controllers.py:31-50` e `74-90` | A mesma validação de produto está escrita duas vezes, e a de categoria só no criar | A atualização já divergiu da criação |
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

A Fase 3 inventaria método, caminho, status e chaves antes da primeira edição. Rota que o `api.http` chama sem credencial continua aceitando a chamada sem credencial. Campo que vaza senha, hash ou número do cartão pode sair da resposta. SQL enviado pelo cliente deixa de executar. A rota e a chave de erro permanecem. O login com a senha do seed continua válido. O hash novo aceita MD5 ou texto puro uma vez e regrava.

Monolito e task manager usam a mesma skill. O monolito recebe pasta nova. O task manager recebe um controller sobre o que já existe. Os dois sobem depois da refatoração.

### Desafios

- `check_same_thread=False` entra em AP-06 como estado global. O playbook usa `flask.g` para cada request do Flask ter a própria conexão.
- Hash novo quebra o seed se o login só comparar digest. PB-07 mantém o caminho legado.
- `Query.get` é API obsoleta (MEDIUM). N+1 é outro achado (MEDIUM), mesmo quando os dois aparecem na mesma linha. A correção trata os dois em separado.
- O serviço de e-mail que fazia `print` segue fazendo `print`.

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
| code-smells-project | `app.py`, `controllers.py`, `models.py`, `database.py` | `app.py` fino, `config/`, `models/`, `controllers/`, `views/routes.py`, `middlewares/` |
| ecommerce-api-legacy | `src/app.js`, `AppManager.js`, `utils.js` | `src/app.js` fino, `config/`, `models/`, `controllers/`, `views/routes.js`, `middlewares/` |
| task-manager-api | `models/`, `routes/` gordas, `services/`, `utils/` | As pastas permanecem. Entraram `controllers/`, `config/` e `middlewares/`. A rota só encaminha. O ORM ficou |

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

Mudanças de contrato feitas de propósito, porque o relatório pedia:

- Loja: `/health` não devolve mais `secret_key`. Listagem de usuário não devolve `senha`. `POST /admin/query` responde 400 `Query não permitida` e não executa o SQL. Login com `joao@email.com` / `123456` continua 200.
- LMS: sucesso do checkout, o texto `Pagamento recusado` e o texto do delete permanecem. O número do cartão e a chave do gateway saíram do log.
- Tarefas: login continua 200 com a senha do seed `1234`, sem o campo `password` e sem o token fictício.

Boot e chamadas reais:

```
code-smells-project  python app.py
GET /health   200   sem secret_key
GET /produtos 200
POST /login   200   joao@email.com / 123456, sem senha no JSON
POST /admin/query {"sql":"DROP TABLE usuarios"}  400  Query não permitida
```

```
ecommerce-api-legacy  npm start
POST /api/checkout cartão 4111...   200  {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout cartão 5111...   400  Pagamento recusado
GET  /api/admin/financial-report    200  Clean Architecture 997 e Docker 497
DELETE /api/users/1                 200  texto original de matrículas órfãs
```

```
task-manager-api  python seed.py && python app.py
GET /health            200
GET /tasks             200
GET /reports/summary   200
POST /login            200  joao@email.com / 1234, sem password e sem token
```

O cliente de teste do Flask cobriu o restante das rotas da loja (18 chamadas) e do task manager (listagem, busca, stats, usuários, categorias, criação e login inválido), sem falha.

### O que a skill fez de diferente em cada stack

No Flask monolítico os findings graves são SQL e o módulo único. No Express o grave é a classe que é o processo, mais segredo e cartão no log; o SQL de negócio já usa `?`, então AP-01 não dispara à toa. No Flask com camadas a skill não finge God class: marca rota gorda, MD5, `create_all` no import e a API obsoleta do ORM. O mesmo catálogo, três desenhos.

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

`GET http://localhost:5000/health` responde 200. `GET http://localhost:5000/produtos` devolve a lista do seed. O JSON de health não traz `secret_key`.

```bash
cd ecommerce-api-legacy
npm install
npm start
```

Os três pedidos de `api.http` continuam válidos na porta 3000: checkout com cartão `4111...` em 200, cartão `5111...` em 400 com o texto `Pagamento recusado`, relatório em 200 e delete em 200.

```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py
```

`GET http://localhost:5000/health`, `GET /tasks`, `POST /login` com `joao@email.com` e `1234`. O login segue aceitando a senha do seed e o JSON não traz `password`.
