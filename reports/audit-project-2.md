# ARCHITECTURE AUDIT REPORT

- Project: ecommerce-api-legacy
- Stack: JavaScript + Express ^4.18.2 (resolvido 4.22.1)
- Files: 3 analyzed | 180 lines
- Architecture: Monolítica
- DB: SQLite em memória (`:memory:`) | tables: `users`, `courses`, `enrollments`, `payments`, `audit_logs`

## Summary

CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] Segredos e credenciais hardcoded na configuração — AP-02
- File: src/utils.js:3-4
- Description: O objeto `config` fixa literais sensíveis diretamente no código-fonte, incluindo `dbPass` (linha 3) e a chave de gateway `paymentGatewayKey` com prefixo `pk_live_` (linha 4), além de `dbUser` (linha 2) e `smtpUser` (linha 5).
- Evidence: `dbPass: "senha_super_secreta_prod_123",`
- Impact: Segredos ficam versionados no repositório e expostos a qualquer pessoa ou processo com acesso ao código.
- Recommendation: Mover todas as credenciais e chaves para variáveis de ambiente lidas por um módulo dedicado de configuração e documentá-las em `.env.example`.
- Playbook: PB-02

### [CRITICAL] Exposição de número de cartão e chave de gateway em log — AP-02
- File: src/AppManager.js:45
- Description: A rota `POST /api/checkout` imprime no `console.log` o número completo do cartão (`cc`) recebido na requisição junto com `config.paymentGatewayKey`.
- Evidence: ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);``
- Impact: Dados de cartão (PAN) e chave de gateway de pagamento vazam em texto puro para stdout e sistemas de coleta de logs.
- Recommendation: Remover o log do número de cartão e da chave do gateway; se necessário registrar eventos de pagamento, emitir apenas metadados não sensíveis.
- Playbook: PB-02

### [CRITICAL] Hash de senha caseiro e reversível em Base64 — AP-04
- File: src/utils.js:17-23
- Description: A função `badCrypto`, chamada na criação de usuário em `src/AppManager.js:68`, concatena em laço os dois primeiros caracteres do Base64 da senha e trunca o resultado para 10 caracteres, sem salt nem algoritmo criptográfico.
- Evidence: `hash += Buffer.from(pwd).toString('base64').substring(0, 2);`
- Impact: Qualquer senha com o mesmo prefixo produz o mesmo valor e o conteúdo é trivialmente reversível em caso de vazamento do banco.
- Recommendation: Substituir `badCrypto` por hash criptográfico com salt por usuário usando `crypto.scrypt` ou `crypto.pbkdf2` do Node.js.
- Playbook: PB-07

### [CRITICAL] Senha de usuário gravada em texto puro no seed — AP-04
- File: src/AppManager.js:18
- Description: O método `initDb` insere o usuário inicial na tabela `users` com a senha `'123'` em texto puro na coluna `pass`.
- Evidence: `this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");`
- Impact: Um vazamento do banco expõe imediatamente a credencial do usuário inicial sem qualquer proteção criptográfica.
- Recommendation: Aplicar o mesmo hash criptográfico com salt ao persistir a senha do usuário no seed de inicialização.
- Playbook: PB-07

### [CRITICAL] God class acumulando banco, rotas HTTP e regras de negócio — AP-03
- File: src/AppManager.js:4-139
- Description: A classe `AppManager` concentra em um único arquivo a abertura da conexão SQLite (linha 7), criação de schema e seed de 5 tabelas (linhas 10-23), definição de todas as rotas HTTP (linhas 25-138), validação de payload, pagamento, matrículas, auditoria, relatório financeiro e exclusão de usuários.
- Evidence: `class AppManager {`
- Impact: Impossibilita testar regras de domínio isoladamente sem subir o banco e o Express, além de acoplar qualquer mudança a um único arquivo central.
- Recommendation: Quebrar `AppManager` em módulos de configuração/banco, models por entidade, controllers de domínio e rotas Express enxutas.
- Playbook: PB-03

### [HIGH] Rota administrativa de relatório financeiro sem autenticação ou autorização — AP-07
- File: src/AppManager.js:80
- Description: O endpoint `GET /api/admin/financial-report` (linhas 80-129) retorna receita agregada por curso e lista de alunos com valores pagos sem validar sessão, token assinado ou chave administrativa, e o projeto não possui nenhuma camada de autorização.
- Evidence: `app.get('/api/admin/financial-report', (req, res) => {`
- Impact: Qualquer cliente anônimo acessa dados financeiros completos e nomes de alunos da plataforma.
- Recommendation: Proteger a rota com middleware de autenticação e verificação de privilégio administrativo, retornando `401` sem credencial válida e `403` sem permissão.
- Playbook: PB-12

### [HIGH] Rota destrutiva de exclusão de usuário sem autenticação ou autorização — AP-07
- File: src/AppManager.js:131
- Description: O endpoint `DELETE /api/users/:id` (linhas 131-137) apaga qualquer usuário pelo parâmetro `id` sem exigir autenticação ou autorização administrativa.
- Evidence: `app.delete('/api/users/:id', (req, res) => {`
- Impact: Qualquer cliente anônimo pode excluir contas de usuários arbitrariamente e deixar matrículas e pagamentos órfãos no banco.
- Recommendation: Proteger a rota com middleware de autenticação/autorização administrativa (`401`/`403`) e tratar a integridade referencial na camada de dados.
- Playbook: PB-12

### [HIGH] Rotas gordas com validação, regra de negócio e SQL direto no handler HTTP — AP-05
- File: src/AppManager.js:28-78
- Description: O handler de `POST /api/checkout` executa diretamente validação de entrada, queries SQL em `courses`, `users`, `enrollments`, `payments` e `audit_logs`, regra de aprovação de pagamento e escrita em cache; o mesmo acoplamento ocorre em `GET /api/admin/financial-report` (linhas 80-129) e `DELETE /api/users/:id` (linhas 131-137).
- Evidence: `app.post('/api/checkout', (req, res) => {`
- Impact: As regras de negócio ficam presas ao ciclo de `req`/`res` do Express, impedindo reuso e exigindo testes HTTP ponta a ponta para qualquer verificação.
- Recommendation: Extrair a orquestração para controllers dedicados e encapsular o acesso SQL em models, deixando as rotas responsáveis apenas pelo roteamento.
- Playbook: PB-04

### [HIGH] Estado global mutável compartilhado entre requisições — AP-06
- File: src/utils.js:9-15
- Description: O módulo exporta `globalCache` (linha 9) e `totalRevenue` (linha 10) como estado global mutável, e `logAndCache` (linhas 12-15) altera `globalCache` a cada checkout em `src/AppManager.js:59`.
- Evidence: `let globalCache = {};`
- Impact: Requisições concorrentes e testes compartilham e corrompem estado em memória, dificultando isolamento e previsibilidade.
- Recommendation: Eliminar estado global mutável de módulo e injetar dependências (como cache ou repositórios) a partir da composição no boot.
- Playbook: PB-06

### [MEDIUM] Consultas N+1 dentro de laços com sincronização manual de callbacks — AP-08
- File: src/AppManager.js:89-127
- Description: Em `GET /api/admin/financial-report`, após buscar todos os cursos (linha 83), um `forEach` executa uma query de matrículas por curso (linha 92) e um `forEach` interno dispara mais duas queries por matrícula em `users` (linha 104) e `payments` (linha 106), usando contadores manuais `coursesPending` e `enrPending` para decidir quando enviar a resposta.
- Evidence: `this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {`
- Impact: O número de consultas cresce multiplicativamente com cursos e matrículas, e falhas intermediárias nos callbacks podem travar ou duplicar a resposta HTTP.
- Recommendation: Substituir as consultas aninhadas por uma única query SQL com `LEFT JOIN` (ou `async/await` com consulta agregada) na camada de model.
- Playbook: PB-05

### [MEDIUM] Tratamento de erro engolido e respostas inconsistentes entre texto e JSON — AP-11
- File: src/AppManager.js:133-136
- Description: O callback de `DELETE /api/users/:id` ignora o parâmetro `err` e sempre responde sucesso em texto; callbacks nas linhas 57, 92, 104 e 106 também não tratam `err`. Além disso, a API mistura `res.send("texto")` em erros (linhas 35, 38, 41, 48, 51, 55, 70, 84, 135) com `res.json(...)` em sucessos (linhas 60, 87, 98, 121), sem middleware centralizado de erro em `src/app.js`.
- Evidence: `this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {`
- Impact: Falhas de banco passam despercebidas ou derrubam o processo em exceções não tratadas, e o cliente recebe formatos de resposta inconsistentes.
- Recommendation: Verificar e propagar todos os erros para um middleware centralizado de 4 argumentos no Express, mantendo o contrato de resposta consistente.
- Playbook: PB-09

### [MEDIUM] Uso da API obsoleta sqlite3.verbose() baseada em callbacks — AP-10
- File: src/AppManager.js:1
- Description: O módulo inicializa o driver `sqlite3` chamando `.verbose()`, que ativa o modo legado de rastreamento de stack orientado a callbacks.
- Evidence: `const sqlite3 = require('sqlite3').verbose();`
- Impact: Mantém o acesso a dados preso ao estilo legado de callbacks aninhados e adiciona overhead desnecessário de rastreamento em runtime.
- Recommendation: Remover `.verbose()` e encapsular o driver `sqlite3` em um wrapper baseado em `Promise`/`async-await` na camada de banco.
- Playbook: PB-08

### [LOW] Identificadores crípticos e literais mágicos no fluxo de checkout — AP-12
- File: src/AppManager.js:29-33
- Description: O checkout atribui campos de domínio a variáveis crípticas (`u`, `e`, `p`, `cid`, `cc`) e embute literais mágicos de regra sem constante nomeada, como o prefixo `"4"` para aprovação do cartão (linha 46) e a senha padrão `"123456"` (linha 68).
- Evidence: `let u = req.body.usr;`
- Impact: Reduz a legibilidade do fluxo de negócio e dificulta manutenção de regras de validação e pagamento.
- Recommendation: Renomear as variáveis internas para nomes descritivos de domínio e extrair literais de regra para constantes nomeadas.
- Playbook: PB-11

### [LOW] Import e variável global não utilizados — AP-12
- File: src/AppManager.js:2
- Description: `AppManager.js` importa `totalRevenue` de `./utils`, mas nunca utiliza o símbolo; em `src/utils.js:10`, `totalRevenue` também é declarado e exportado sem nenhum uso no projeto.
- Evidence: `const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');`
- Impact: Gera código morto e ruído na leitura das dependências entre módulos.
- Recommendation: Remover o import não utilizado `totalRevenue` e a declaração ociosa correspondente.
- Playbook: PB-11

### [LOW] Log de debug no fluxo feliz de requisições — AP-12
- File: src/utils.js:13
- Description: A função `logAndCache` executa `console.log` a cada gravação em cache durante o fluxo normal de checkout.
- Evidence: ``console.log(`[LOG] Salvando no cache: ${key}`);``
- Impact: Polui a saída padrão em produção com mensagens de depuração sem estrutura.
- Recommendation: Remover o `console.log` de debug do fluxo feliz ou substituí-lo por logging estruturado controlável por ambiente.
- Playbook: PB-11

## Deprecated APIs

- `sqlite3.verbose()` em `src/AppManager.js:1` → `node:sqlite` ou wrapper com `Promise` em volta de `sqlite3` sem `verbose()`

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
