# Playbook de refatoração

Oito padrões obrigatórios e quatro complementares. Aplique só os ligados a findings do relatório. Cada um tem o antes, o depois e a armadilha que quebra o contrato.

## PB-01 — SQL concatenada para parâmetro

Antes (Python):

```python
cursor.execute("SELECT * FROM itens WHERE id = " + str(id))
cursor.execute("INSERT INTO itens (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")")
```

Depois:

```python
cursor.execute("SELECT * FROM itens WHERE id = ?", (id,))
cursor.execute(
    "INSERT INTO itens (nome, preco) VALUES (?, ?)",
    (nome, preco),
)
```

Antes (JavaScript):

```javascript
db.get(`SELECT * FROM users WHERE email = '${email}'`, callback)
```

Depois:

```javascript
db.get("SELECT * FROM users WHERE email = ?", [email], callback)
```

Filtro dinâmico: monte o SQL só com fragmentos escritos no código (`" AND preco >= ?"`) e empurre o valor para a lista de parâmetros. Nunca concatene o valor.

Rota que executa SQL do cliente: mantenha método e caminho; não chame `execute` com essa string; responda com o status de erro já usado para entrada inválida e a chave de erro do projeto (`erro` ou `error`).

## PB-02 — Segredo para o módulo de config

Antes:

```python
app.config["SECRET_KEY"] = "hardcoded-secret"

return jsonify({"status": "ok", "secret_key": "hardcoded-secret"})
```

Depois:

```python
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

return jsonify({"status": "ok"})
```

O mesmo para Node: `process.env.PAYMENT_GATEWAY_KEY` num `config/settings.js`, e o `console.log` deixa de imprimir cartão e chave. Log de pagamento registra status e id, não o PAN.

`.env.example` lista `SECRET_KEY=`, `PAYMENT_GATEWAY_KEY=`, `SMTP_PASSWORD=`. O valor real não vai para o git.

## PB-03 — God module para MVC

Antes:

```python
def criar_fatura(cliente_id, linhas):
    # SQL do item, regra de estoque, insert da fatura e da linha
    ...

def resumir_faturamento():
    # SQL e alíquota no mesmo módulo
    ...
```

Depois:

```python
def criar(cliente_id, linhas):
    return fatura_model.inserir(cliente_id, total, linhas)

def criar_fatura(cliente_id, linhas):
    erro = validar_estoque(linhas)
    if erro:
        return erro
    return {"fatura_id": criar(cliente_id, linhas), "total": total}
```

O primeiro bloco fica em `models/fatura_model.py`. O segundo, em `controllers/fatura_controller.py`. A view só registra a rota. O mesmo vale para uma classe que abre o banco e registra rotas: o método da rota não permanece nessa classe.

Ordem segura: extrair a persistência sem mudar o caminho HTTP, apontar os callers, só então apagar o arquivo antigo.

## PB-04 — Rota fina, controller orquestra

Antes:

```python
@bp.route("/faturas", methods=["POST"])
def criar_fatura():
    dados = request.get_json()
    total = 0
    for linha in dados["linhas"]:
        item = query_item(linha["item_id"])
        if item["estoque"] < linha["quantidade"]:
            return jsonify({"erro": "Estoque insuficiente"}), 400
        total += item["preco"] * linha["quantidade"]
    fatura_id = insert_fatura(dados["cliente_id"], total)
    return jsonify({"dados": {"fatura_id": fatura_id, "total": total}, "sucesso": True}), 201
```

Depois:

```python
def criar_fatura(dados):
    if not dados or not dados.get("linhas"):
        return {"erro": "Fatura deve ter pelo menos 1 linha"}, 400
    resultado = calcular_e_gravar(dados["cliente_id"], dados["linhas"])
    if "erro" in resultado:
        return resultado, 400
    return {"dados": resultado, "sucesso": True, "mensagem": "Fatura criada com sucesso"}, 201

@bp.route("/faturas", methods=["POST"])
def criar_fatura_view():
    body, status = criar_fatura(request.get_json(silent=True))
    return jsonify(body), status
```

Efeito colateral que já existia (log de "e-mail enviado") pode permanecer no controller como log. Não passe a enviar e-mail de verdade se antes era só `print`: isso muda comportamento e depende de rede.

## PB-05 — N+1 para uma consulta ou mapa

Antes:

```python
for fatura in faturas:
    linhas = query("SELECT * FROM fatura_linhas WHERE fatura_id = " + str(fatura["id"]))
    for linha in linhas:
        nome = query("SELECT nome FROM itens WHERE id = " + str(linha["item_id"]))
```

Depois:

```python
linhas = query(
    """
    SELECT l.*, i.nome AS item_nome
    FROM fatura_linhas l
    JOIN itens i ON i.id = l.item_id
    WHERE l.fatura_id IN ({})
    """.format(",".join("?" * len(ids))),
    ids,
)
```

Os placeholders são `?` repetidos, não os ids. Os ids viajam na tupla.

No ORM:

```python
faturas = Fatura.query.options(
    joinedload(Fatura.cliente),
    joinedload(Fatura.linhas),
).all()
```

Use a relação que já existe no model. Não abra `Cliente.query.get` dentro do `for`.

Callbacks aninhados com contador manual de pendências para responder: troque por uma query que já devolve o pai e os filhos, ou por `Promise` encadeada com um único envio de resposta. A forma do JSON de saída permanece.

## PB-06 — Estado global para o boot

Antes:

```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
```

Depois: abrir a conexão no escopo da aplicação, uma função `get_db` que usa `flask.g` (ou o equivalente do framework) e fecha no teardown. Sem `check_same_thread=False`.

```python
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

Cache em memória: objeto criado no boot e injetado no controller, não uma variável mutável exportada em módulo utilitário compartilhado entre requisições. Acumuladores globais em memória devem ser removidos ou substituídos por consulta agregada no banco.

`db.create_all()` vai para o bloco de boot (`__main__` ou factory chamada pelo processo), não no import. Importar o módulo deixa de criar arquivo e tabela.

## PB-07 — Senha que autentica depois do hash

Antes:

```python
self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```

Depois:

```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    if check_password_hash(self.password, pwd):
        return True
    legacy = hashlib.md5(pwd.encode()).hexdigest()
    if self.password == legacy or self.password == pwd:
        self.password = generate_password_hash(pwd)
        return True
    return False
```

`to_dict` e o JSON de login não incluem `password`, `senha` nem `pass`. O commit do upgrade legado acontece no fluxo de login que já gravava sessão, para a próxima tentativa usar o hash novo. A senha dos dados de exemplo continua válida.

Se o projeto não verifica senha em lugar nenhum, grave hash novo e não invente rota de login.

## PB-08 — API obsoleta, substituto moderno

Troca mecânica, uma a uma, com o mesmo comportamento:

| Antes | Depois |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `Model.query.get(id)` | `db.session.get(Model, id)` |
| `require('body-parser')` + `bodyParser.json()` | `express.json()` |
| `app.del('/x', h)` | `app.delete('/x', h)` |
| `res.sendfile(path)` | `res.sendFile(path)` |
| `new Buffer(s)` | `Buffer.from(s)` |
| `sqlite3.verbose()` | `require('sqlite3')` sem verbose, ou `node:sqlite` se o runtime do projeto for Node 22+ e o README permitir |
| `@app.before_first_request` | chamada direta no factory, antes de servir |

`datetime.now(timezone.utc)` é timezone-aware. Comparação com valor vindo do banco pode misturar aware e naive. Se o model gravava naive, normalize na leitura ou use helper central de relógio para que comparações de prazo/expiração continuem equivalentes. Não mude o formato da string que a API já devolve se o cliente recebe `str(data)`.

Não reescreve todas as `Model.query.filter` para `select()` nesta passagem. Só o `.query.get` está na tabela obsoleta.

## PB-09 — Um handler de erro

Antes: cada função com `except Exception as e: return jsonify({"erro": str(e)}), 500`.

Depois: a função propaga, ou devolve erro de negócio já conhecido (`400` de validação). O handler:

```python
@app.errorhandler(Exception)
def handle_unexpected(error):
    app.logger.exception("unhandled")
    return jsonify({"erro": "Erro interno"}), 500
```

Preserve a chave (`erro` ou `error`) que o projeto já usa. Mensagem de validação escrita no código permanece. `str(e)` de `OperationalError` não volta ao cliente.

JavaScript:

```javascript
function errorHandler(err, req, res, next) {
    console.error(err);
    res.status(500).json({ error: "Erro interno" });
}
```

Middleware de erro por último, com quatro parâmetros. Onde a rota respondia texto puro (`res.status(400).send("Bad Request")`), ela continua respondendo texto puro. O handler só unifica o que era exceção.

## PB-10 — Uma regra, um lugar

Antes:

```python
if fatura.vencimento and fatura.vencimento < datetime.now(timezone.utc) and fatura.status not in ("paga", "cancelada"):
    data["vencida"] = True
```

A mesma condição aparece na listagem, no detalhe, no relatório e no model, escritos à mão.

Depois:

```python
data["vencida"] = fatura.esta_vencida()
```

Escolha o helper ou o método de model que já tem a regra. Apague as cópias da rota e chame esse lugar. Se não existir, crie uma função única de validação/regra no controller ou em módulo de validação e use em todas as operações equivalentes (como criar e atualizar).

Constantes de limite (tamanhos mínimos/máximos, status válidos, faixas ou alíquotas) ficam ao lado da regra, com o número que já estava no código. Não altere os valores de negócio.

## PB-11 — Nome, número mágico, import morto

- Renomeie variáveis crípticas ou de uma letra (como `x`, `a`, `b`, `tmp`) para o substantivo do domínio quando mexer no bloco por outro playbook. Não faça um diff só de rename.
- Substitua o número literal da regra pela constante de PB-10 quando ela já existir e a rota a ignorava.
- Apague import não usado no arquivo que você abriu para outro finding. Não varra o projeto inteiro atrás de import.

## PB-12 — Proteção de rotas destrutivas e administrativas

Toda rota destrutiva, administrativa ou de escalação de privilégio apontada por `AP-07` na Fase 2 DEVE ser protegida na Fase 3, sem adicionar dependências externas fora do stack já instalado. Escolha a estratégia conforme o projeto já possuir fluxo de login ou não:

### Estratégia A — Projeto com autenticação (`/login`) e papéis (ex.: Python/Flask)

Antes:

```python
@app.route("/login", methods=["POST"])
def login():
    return jsonify({"account": account.to_dict(), "token": "static-token-" + str(account.id)}), 200

@app.route("/admin/maintenance", methods=["POST"])
def run_maintenance():
    ...
```

Depois:

```python
# middlewares/auth.py (usando serializer assinado nativo do stack, ex.: itsdangerous no Flask)
from functools import wraps
from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from config.settings import SECRET_KEY, TOKEN_MAX_AGE

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="app-auth")

def gerar_token(conta):
    return _serializer.dumps({"id": conta["id"], "email": conta["email"], "role": conta["role"]})

def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify({"erro": "Autenticação obrigatória"}), 401
            try:
                payload = _serializer.loads(header[7:].strip(), max_age=TOKEN_MAX_AGE)
            except (BadSignature, SignatureExpired):
                return jsonify({"erro": "Token inválido ou expirado"}), 401
            if roles and payload.get("role") not in roles:
                return jsonify({"erro": "Permissão insuficiente"}), 403
            g.current_user = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

- A rota de login passa a retornar um `token` assinado real (mantendo os demais campos de sucesso existentes).
- Rotas destrutivas ou administrativas (reset/manutenção, exclusões sensíveis, relatórios gerenciais) recebem middleware de autenticação/autorização (`401` sem token válido, `403` sem permissão ou fora da propriedade do recurso).
- Criação e atualização de contas impedem auto-promoção anônima de papel privilegiado: apenas administrador autenticado pode atribuir ou alterar papel privilegiado (`403` caso contrário).

### Estratégia B — Projeto sem fluxo de login (ex.: Node.js/Express)

Antes:

```javascript
app.delete('/api/records/:id', (req, res) => {
    ...
});
```

Depois:

```javascript
// src/middlewares/authMiddleware.js
const crypto = require("crypto");
const { config } = require("../config/settings");

function requireAdmin(req, res, next) {
    const authHeader = req.headers.authorization || "";
    const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
    const provided = req.headers["x-admin-key"] || bearer;
    if (!provided) {
        return res.status(401).json({ error: "Credencial administrativa obrigatória" });
    }
    const a = Buffer.from(String(provided));
    const b = Buffer.from(String(config.adminApiKey));
    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
        return res.status(403).json({ error: "Credencial administrativa inválida" });
    }
    return next();
}
```

- `ADMIN_API_KEY` é lida no módulo de `config` e documentada em `.env.example` (com fallback local explícito apenas para desenvolvimento).
- Rotas destrutivas e administrativas aplicam o middleware de autorização na camada de rotas; arquivos `.http` ou exemplos do repositório são atualizados com o header administrativo.
- Se existir rota que executava SQL arbitrário do cliente, combine `PB-12` (`401`/`403` para não-admin) com `PB-01` (recusa `400` mesmo autenticado).
- Em exclusões de registros com entidades filhas, remova os registros dependentes em transação no repositório para não deixar órfãos no banco.
- Registre todas as proteções no log de validação como mudanças intencionais de segurança.

## Ordem de aplicação

1. PB-02 e PB-07 (segredo e senha), porque atravessam resposta.
2. PB-01 (SQL).
3. PB-06 (estado no boot), antes de espalhar callers do `get_db` novo.
4. PB-03 ou PB-04, conforme o modo de migração.
5. PB-05, PB-08, PB-09, PB-10.
6. PB-11 por último, e só no arquivo já tocado.
7. PB-12 junto de PB-01.

Depois da ordem, rode a validação das guidelines. Diff que não está ligado a um finding do relatório se desfaz.
