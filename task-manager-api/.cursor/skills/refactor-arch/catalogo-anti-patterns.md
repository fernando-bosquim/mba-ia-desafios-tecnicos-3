# Catálogo de anti-patterns

Use na Fase 2. Um finding por ocorrência lógica: o mesmo padrão em um arquivo pode ser um finding com várias linhas; o mesmo padrão em responsabilidades diferentes (persistência versus rota) vira findings separados. Não junte SQL injection com God module só porque estão no mesmo arquivo.

Severidade:

| Nível | Quando usar |
|---|---|
| CRITICAL | Quebra segurança ou a separação de responsabilidades por completo: injeção, segredo exposto, senha reversível, God module/class com dados + regra + borda HTTP |
| HIGH | MVC ou SOLID comprometidos a ponto de dificultar teste e mudança: regra de negócio presa na rota, estado global mutável, acoplamento forte sem fronteira de dependência |
| MEDIUM | Duplicação, N+1, validação ausente, erro inconsistente, API obsoleta |
| LOW | Nome, número mágico, print de debug, import morto, constante ignorada |

Cada finding precisa de: id do catálogo, severidade, arquivo, linhas, descrição do que a linha faz, impacto, recomendação de uma ou duas frases, id do playbook.

## AP-01 — SQL concatenada ou SQL arbitrário

- Severidade: CRITICAL
- Sinais: valor de request, parâmetro ou f-string entra no texto SQL. Em Python: `"SELECT ..." +`, f-string com variável na query, `"%s" %` com valor externo, `.format` na query. Em JavaScript: template `` `SELECT ... ${...}` `` ou `"SELECT " +` com dado externo. Também: rota que executa SQL recebido no corpo (`req.body.sql`, `dados["sql"]`, `cursor.execute(query)` quando `query` veio do cliente).
- Não é finding: `?`, `%s` com tupla, `$1`, `db.session` / ORM sem texto montado, concatenação só de cláusulas fixas escritas no código.
- Impacto: leitura e escrita fora do contrato da aplicação.
- Correção: PB-01.

## AP-02 — Segredo no código ou na resposta

- Severidade: CRITICAL
- Sinais: literal de `SECRET_KEY`, senha, token, API key, chave de gateway (`pk_live`, `sk_live`, `AKIA`), senha de SMTP, atribuído no fonte. O mesmo literal devolvido em JSON (`secret_key`, `password`, `senha`, `pass`). Cartão (PAN) em `console.log`, `print` ou logger.
- Não é finding: nome de variável sem literal; porta; usuário de seed sem senha; placeholder vazio.
- Impacto: segredo versionado e, quando ecoado, vazado para quem chama a API.
- Correção: PB-02.

## AP-03 — God module ou God class

- Severidade: CRITICAL
- Sinais: o mesmo arquivo acumula duas ou mais destas responsabilidades para mais de uma entidade: SQL ou DDL, regra de negócio (preço, estoque, status, pagamento), borda HTTP, segredo, notificação. Vale para `class` e para módulo de funções soltas. Sinal forte: um arquivo "manager", "utils" ou `models.py` único cobrindo o domínio inteiro.
- Não é finding: model com método que só olha os próprios campos (`is_overdue` da entidade). Rota que só registra URL. Arquivo grande que faz uma coisa só.
- Impacto: não dá para testar um domínio sem subir o resto; qualquer mudança atravessa o arquivo.
- Correção: PB-03.

## AP-04 — Senha reversível ou hash obsoleto

- Severidade: CRITICAL se a senha é texto puro, MD5, SHA1, ou hash caseiro. HIGH se o hash moderno existe mas o hash ou a senha volta no JSON.
- Sinais: coluna `senha` / `password` / `pass` gravada com o valor recebido; `hashlib.md5` ou `hashlib.sha1` em senha; loop que "embaralha" base64 ou substring e chama isso de hash; `to_dict` ou resposta de login com o campo de senha.
- Não é finding: `generate_password_hash`, bcrypt, scrypt, argon2, PBKDF2, quando o digest não é serializado na resposta.
- Impacto: vazamento do banco revela a senha; MD5 e SHA1 não servem para senha.
- Correção: PB-07.

## AP-05 — Rota ou controller gordo

- Severidade: HIGH
- Sinais: a função ligada à rota valida, decide regra (estoque, desconto, pagamento, status), chama ORM ou SQL e monta notificação. A pasta `routes/` ou `controllers/` existe, mas não há camada abaixo da HTTP. Entry point (`app.py`, `app.js`) executa `DELETE`/`INSERT` ou abre transação.
- Não é finding: rota com três linhas que chama um controller. Validação de presença de campo na borda, se a regra de domínio está no controller ou num validador único.
- Impacto: a regra não roda sem request; teste vira teste de HTTP.
- Correção: PB-04.

## AP-06 — Estado global mutável

- Severidade: HIGH
- Sinais: `global` de conexão, cache ou contador; `let cache = {}` exportado e mutado; conexão criada uma vez com `check_same_thread=False`; objeto de domínio instanciado no import e reutilizado entre requests com campos que mudam; `create_all()` ou `initDb()` no import do módulo, não na função de boot.
- Não é finding: constante imutável; pool criado no boot e injetado; cache local da função.
- Impacto: requests se cruzam, teste vaza estado, thread do SQLite quebra fora do thread criador.
- Correção: PB-06.

## AP-07 — Operação privilegiada sem fronteira

- Severidade: HIGH quando a rota apaga dados, executa SQL livre, muda papel de usuário ou lê relatório financeiro completo, e não existe nenhuma função de autorização no projeto. MEDIUM quando a autorização existe e esta rota simplesmente não a chama.
- Sinais: `reset`, `admin`, `delete` em massa, `role` definido pelo cliente, relatório agregado, sem leitura de sessão, token ou header em nenhum ponto do fluxo.
- Não é finding para corrigir com 401 na Fase 3 se os clientes atuais chamam a rota sem credencial. Registre o achado. A única correção obrigatória na Fase 3 é fechar SQL arbitrário (AP-01).
- Impacto: qualquer cliente opera como administrador.
- Correção: PB-12.

## AP-08 — N+1 e consulta dentro de laço

- Severidade: MEDIUM
- Sinais: `query`, `SELECT`, `.get(`, `.filter`, `db.get` ou `db.all` dentro de `for`, `forEach` ou `.map` sobre linhas que acabaram de ser lidas. Contador manual de callbacks (`pending--`) para saber quando a resposta pode ser enviada.
- Não é finding: join ou `IN (...)` único; eager load; laço que só monta dicionário em memória.
- Impacto: tempo cresce com o número de pais × filhos; em callback, a resposta pode sair duplicada ou nunca sair.
- Correção: PB-05.

## AP-09 — Duplicação de regra

- Severidade: MEDIUM
- Sinais: o mesmo bloco de validação, o mesmo cálculo de atraso, o mesmo mapeamento linha→dicionário, copiado em duas funções. Helper ou método de model com a regra, enquanto a rota reimplementa o bloco e não chama o helper.
- Não é finding: duas funções que compartilham um validador. CRUD parecido com campos diferentes.
- Impacto: uma correção precisa ser feita em N lugares e alguma fica velha.
- Correção: PB-10.

## AP-10 — API obsoleta

- Severidade: MEDIUM. Se a API obsoleta também for senha fraca, o finding de senha fica em AP-04 (CRITICAL) e esta linha só entra na seção de APIs obsoletas do relatório.
- Varredura obrigatória. Procure estes sinais e registre o substituto. Ausência também se declara.

| Sinal | Onde dói | Substituto |
|---|---|---|
| `datetime.utcnow` e `datetime.datetime.utcnow` | Python 3.12, deprecado | `datetime.now(timezone.utc)` |
| `.query.get(` | SQLAlchemy 2 / Flask-SQLAlchemy 3, API legada de `Query` | `db.session.get(Modelo, id)` |
| `hashlib.md5` ou `hashlib.sha1` em senha | algoritmo obsoleto para senha | `werkzeug.security.generate_password_hash` ou PBKDF2 |
| `sqlite3.verbose()` | modo de trace do driver antigo, callback | `node:sqlite` ou wrapper com `Promise` em volta de `sqlite3` sem `verbose()` |
| `require('body-parser')` ou `bodyParser()` | pacote absorvido pelo Express 4.16+ | `express.json()` e `express.urlencoded()` |
| `app.del(` | removido no Express 4 | `app.delete(` |
| `res.sendfile(` | renomeado | `res.sendFile(` |
| `new Buffer(` | Node, deprecado | `Buffer.from(` |
| `@app.before_first_request` | removido no Flask 2.3+ | registrar o setup no factory, antes do `run` |

- Não é finding: `express.json()`, `app.delete`, `Buffer.from`, `datetime.now(timezone.utc)`, `db.session.get`.
- Correção: PB-08.

## AP-11 — Erro espalhado ou engolido

- Severidade: MEDIUM
- Sinais: `except:` ou `catch` vazio; `except Exception` que devolve `str(e)` ao cliente; o mesmo `try/except` colado em toda função da rota; mistura de `res.send("texto")` e `res.json` no mesmo recurso; `print` / `console.log` como único tratamento.
- Não é finding: handler único registrado com `@app.errorhandler` ou middleware de 4 argumentos, e rotas que deixam a exceção subir.
- Impacto: contrato de erro instável e detalhe interno de banco na resposta.
- Correção: PB-09.

## AP-12 — Legibilidade

- Severidade: LOW
- Sinais: número mágico de regra (alíquota, limite, tamanho mínimo) repetido longe de uma constante; variável de uma letra para campo de negócio (`u`, `e`, `p`, `cc`); import não usado; função de helper nunca chamada; `print`/`console.log` de debug no fluxo feliz; `type(x) == list` em vez de `isinstance`.
- Não é finding: índice de laço `i`; constante já nomeada; log estruturado de boot.
- Impacto: leitura lenta, não quebra o desenho.
- Correção: PB-11.

## Ordem de procura sugerida

1. Segredos e senha (AP-02, AP-04).
2. SQL (AP-01).
3. Forma do arquivo (AP-03, AP-05, AP-06).
4. Laços com consulta (AP-08) e cópia (AP-09).
5. Tabela de API obsoleta (AP-10), arquivo por arquivo.
6. Erro (AP-11) e legibilidade (AP-12).

Mínimo do relatório: 5 findings, com pelo menos um CRITICAL ou HIGH, quando o código tiver esse material. Não invente finding para bater cota. Se o projeto já estiver limpo, entregue a lista real e declare a cota no resumo.
