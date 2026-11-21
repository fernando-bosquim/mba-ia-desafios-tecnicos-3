# ARCHITECTURE AUDIT REPORT

- Project: ecommerce-api-legacy
- Stack: JavaScript + Express ^4.18.2
- Files: 3 analyzed | 180 lines
- Architecture: Monolítica — `AppManager` abre o banco, cria o schema e registra as rotas
- DB: SQLite em memória | tables: users, courses, enrollments, payments, audit_logs

## Summary

CRITICAL: 3 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] God class de checkout, relatório e delete — AP-03
- File: src/AppManager.js:3-139
- Description: A classe cria as cinco tabelas, faz seed e implementa checkout, relatório financeiro e exclusão de usuário, com SQL e resposta HTTP nos mesmos métodos.
- Evidence: `setupRoutes(app) {`
- Impact: Não há como testar matrícula sem subir a classe inteira. O arquivo é o sistema.
- Recommendation: Repositório por tabela, controller de checkout e de relatório, rotas finas. A conexão fica no boot.
- Playbook: PB-03

### [CRITICAL] Segredos de produção e PAN no log — AP-02
- File: src/utils.js:3-5
- Description: Senha de banco, chave `pk_live` e usuário SMTP estão no fonte. O checkout escreve o cartão e a chave no stdout em `src/AppManager.js:45`.
- Evidence: `paymentGatewayKey: "pk_live_1234567890abcdef",`
- Impact: O repositório entrega credencial de gateway. Cada checkout grava o número do cartão no log do processo.
- Recommendation: Módulo de config lendo ambiente. Log de pagamento só com status e id de matrícula.
- Playbook: PB-02

### [CRITICAL] Hash de senha caseiro — AP-04
- File: src/utils.js:17-23
- Description: `badCrypto` repete um pedaço do base64 da senha dez mil vezes e devolve dez caracteres. O checkout grava isso na coluna `pass` (`src/AppManager.js:68-69`). Não existe rota que confira a senha depois.
- Evidence: `hash += Buffer.from(pwd).toString('base64').substring(0, 2);`
- Impact: A coluna `pass` não protege a senha. O laço de 10000 ainda custa CPU em todo usuário novo.
- Recommendation: Gravar hash de verdade no insert. Não criar rota de login que o contrato não tinha.
- Playbook: PB-07

### [HIGH] Checkout inteiro dentro da rota — AP-05
- File: src/AppManager.js:28-77
- Description: A closure de `POST /api/checkout` valida o corpo, busca curso, cria usuário, decide pagamento pelo primeiro dígito do cartão e grava matrícula, pagamento e auditoria.
- Evidence: `let status = cc.startsWith("4") ? "PAID" : "DENIED";`
- Impact: A regra do cartão só existe no callback HTTP. Qualquer mudança de cobrança edita a rota.
- Recommendation: Controller devolve status e corpo. A rota lê `req.body` e envia a resposta. Texto `"Bad Request"`, `"Pagamento recusado"` e o JSON `{ msg, enrollment_id }` permanecem.
- Playbook: PB-04

### [HIGH] Cache global mutável — AP-06
- File: src/utils.js:9-14
- Description: `globalCache` é um objeto exportado e alterado por `logAndCache` a cada checkout. `totalRevenue` é exportado e não é lido por ninguém (`src/AppManager.js:2` importa e ignora).
- Evidence: `globalCache[key] = data;`
- Impact: Estado de um request vaza para o próximo. O número de receita global não tem dono.
- Recommendation: Cache criado no boot e injetado, se ainda for necessário. Apagar `totalRevenue` se continuar sem leitor.
- Playbook: PB-06

### [HIGH] Relatório e delete sem fronteira de autorização — AP-07
- File: src/AppManager.js:80
- Description: `GET /api/admin/financial-report` devolve receita e alunos. `DELETE /api/users/:id` (`src/AppManager.js:131-136`) apaga o usuário e deixa matrícula e pagamento órfãos. Nenhuma rota lê credencial. O `api.http` chama as duas sem header.
- Evidence: `app.get('/api/admin/financial-report', (req, res) => {`
- Impact: O relatório administrativo e o delete são públicos. O delete ainda suja `enrollments` e `payments`.
- Recommendation: Não responder 401 nestas rotas. Registrar a dívida de autorização. Órfãos entram na extração do controller, sem mudar o texto da resposta do delete.
- Playbook: PB-12

### [MEDIUM] Consulta por curso, matrícula, usuário e pagamento — AP-08
- File: src/AppManager.js:89-123
- Description: Para cada curso há um `SELECT` de matrículas; para cada matrícula, um `SELECT` de usuário e outro de pagamento. `coursesPending` e `enrPending` decidem quem chama `res.json`. Se `enrollments` vier `undefined` na falha, `enrollments.length` quebra (`src/AppManager.js:93`).
- Evidence: `this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {`
- Impact: Volume de queries explode com o catálogo. Dois callbacks podem responder, ou nenhum responder, no mesmo request.
- Recommendation: Uma consulta que já una curso, matrícula, usuário e pagamento, com um único `res.json` no formato atual (`course`, `revenue`, `students`).
- Playbook: PB-05

### [MEDIUM] Erro em texto e sucesso em JSON — AP-11
- File: src/AppManager.js:35
- Description: Validação, curso ausente, falha de banco e pagamento recusado usam `res.send` com string. O sucesso usa `res.json`. Não há middleware de erro.
- Evidence: `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");`
- Impact: Cliente precisa aceitar dois contratos no mesmo recurso. Exceção fora do callback não tem formato.
- Recommendation: Handler único só para exceção. As strings já escritas nas rotas permanecem.
- Playbook: PB-09

### [MEDIUM] `sqlite3.verbose()` e API só por callback — AP-10
- File: src/AppManager.js:1
- Description: O driver é carregado em modo trace. Todo acesso passa por callback aninhado, que é a superfície antiga desse pacote.
- Evidence: `const sqlite3 = require('sqlite3').verbose();`
- Impact: Trace no boot e fluxo difícil de ordenar. A versão moderna do runtime Node expõe `node:sqlite` síncrono; sem trocar de runtime, o passo seguro é tirar o `verbose()` e isolar a chamada em Promise.
- Recommendation: Remover `.verbose()`. Encapsular `db.get` / `db.run` / `db.all` num repositório. Só migrar para `node:sqlite` se o Node do ambiente for 22 ou mais novo.
- Playbook: PB-08

### [LOW] Campos de uma letra no checkout — AP-12
- File: src/AppManager.js:29-33
- Description: O corpo usa `usr`, `eml`, `pwd`, `c_id` e `card`, e a função reduz isso a `u`, `e`, `p`, `cid` e `cc`.
- Evidence: `let u = req.body.usr;`
- Impact: A regra de pagamento fica ilegível. Os nomes do JSON são o contrato e não podem ser renomeados.
- Recommendation: Variáveis internas com nome de domínio, só no bloco já movido para o controller. As chaves do body permanecem.
- Playbook: PB-11

### [LOW] Senha padrão mágica — AP-12
- File: src/AppManager.js:68
- Description: Usuário sem `pwd` cai em `"123456"` antes do hash caseiro.
- Evidence: `let hash = badCrypto(p || "123456");`
- Impact: Conta criada sem senha fica com um segredo conhecido, ainda por cima mal hasheado.
- Recommendation: Constante nomeada no módulo de usuário, com o mesmo fallback, até o hash de PB-07 entrar.
- Playbook: PB-11

## Deprecated APIs

- `sqlite3.verbose()` em `src/AppManager.js:1` → `require('sqlite3')` sem verbose, ou `node:sqlite` em Node 22+

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
