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

Callback aninhado que conta `pending` para responder: troque por uma query que já devolve o pai e os filhos, ou por `Promise` encadeada com um único `res.json`. A forma do JSON de saída permanece.

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

Cache em Node: objeto criado no boot e injetado no controller, não um `let` exportado de `utils.js` que qualquer rota muta. Contador de faturamento global sai. O total passa a ser consulta, se alguém realmente o lia. Se ninguém lia, apague o estado morto.

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

`datetime.now(timezone.utc)` é timezone-aware. Comparação com valor vindo do banco pode misturar aware e naive. Se o model gravava naive, normalize na leitura (`replace(tzinfo=timezone.utc)` só se o valor for naive) para `is_overdue` continuar verdadeiro nos mesmos casos. Não mude o formato da string que a API já devolve se o cliente recebe `str(data)`.

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
if t.due_date and t.due_date < datetime.now(timezone.utc) and t.status not in ("done", "cancelled"):
    data["overdue"] = True
```

A mesma condição aparece na listagem, no detalhe, no relatório e no model, escritos à mão.

Depois:

```python
data["overdue"] = task.is_overdue()
```

Escolha o helper ou o método de model que já tem a regra. Apague as cópias da rota e chame esse lugar. Se não existir, crie uma função no controller ou em `utils` de validação e use nas duas rotas (criar e atualizar).

Constantes de limite (`MIN_TITLE_LENGTH`, status válidos, alíquotas de desconto) ficam ao lado da regra, com o número que já estava no código. Não "melhore" a alíquota.

## PB-11 — Nome, número mágico, import morto

- Renomeie `u`, `e`, `p`, `cc` para o substantivo do campo quando mexer no bloco por outro playbook. Não faça um diff só de rename.
- Substitua o número da regra pela constante de PB-10 quando ela já existir e a rota ignorava.
- Apague import não usado no arquivo que você abriu para outro finding. Não varra o projeto inteiro atrás de import.

## PB-12 — Privilégio sem quebrar o cliente

Achado AP-07, na Fase 3:

- SQL livre do cliente: aplique PB-01 (recusa).
- Demais rotas administrativas que o exemplo do projeto chama sem credencial: não adicione checagem que devolva 401. Deixe a rota funcionando e descreva no log de validação: "autorização não introduzida para preservar o contrato; finding mantido como dívida".
- `role` vindo do body continua aceito se já era aceito. Não feche isso nesta passagem se o exemplo cria usuário com `role`.

## Ordem de aplicação

1. PB-02 e PB-07 (segredo e senha), porque atravessam resposta.
2. PB-01 (SQL).
3. PB-06 (estado no boot), antes de espalhar callers do `get_db` novo.
4. PB-03 ou PB-04, conforme o modo de migração.
5. PB-05, PB-08, PB-09, PB-10.
6. PB-11 por último, e só no arquivo já tocado.
7. PB-12 junto de PB-01.

Depois da ordem, rode a validação das guidelines. Diff que não está ligado a um finding do relatório se desfaz.
