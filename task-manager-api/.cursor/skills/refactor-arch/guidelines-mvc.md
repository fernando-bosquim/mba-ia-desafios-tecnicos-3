# Guidelines de MVC

Alvo da Fase 3. A pasta pode se chamar `views` ou `routes`: as duas são a camada de borda HTTP. O nome que o projeto já usa permanece.

## Responsabilidades

| Camada | Faz | Não faz |
|---|---|---|
| Config | Lê ambiente, expõe porta, URI, segredo, CORS | SQL, regra, resposta HTTP |
| Model | Tabela, mapeamento, queries parametrizadas, método da própria entidade | `request`, status HTTP, e-mail, regra de outro domínio |
| Controller | Orquestra um caso de uso: valida entrada já parseada, chama model, decide o resultado | Montar SQL por concatenação, conhecer `request` se a view já entregou um dict |
| View / Route | Método, caminho, parse do body/query, traduz resultado em status e JSON | Estoque, preço, pagamento, hash, relatório |
| Middleware de auth | Valida token assinado ou `ADMIN_API_KEY` e verifica papel/permissão antes do controller; devolve `401`/`403` | Regra de negócio ou SQL de domínio |
| Middleware de erro | Um lugar para exceção não tratada e o formato de erro do projeto | Regra de negócio |
| Entry point | Cria app, lê config, registra rotas, sobe o servidor | Query, seed de regra, handler gordo |

Dependência permitida: view → controller → model, e controller → config. Model não importa view nem controller. Config não importa model.

## Modo de migração

Escolha um antes de criar pasta.

1. **Greenfield.** Use quando HTTP, SQL e regra estão nos mesmos arquivos e não existe pacote de domínio. Crie a árvore alvo. O entry point antigo vira composition root fino.
2. **Evolutivo.** Use quando `models/` e `routes/` (ou `services/`) já existem. Acrescente `controllers/`, `config/` e `middlewares/`. A rota fica com o decorator e uma chamada. O model permanece a fonte dos dados. Não reescreva ORM em SQL cru. Preserve a organização já existente que respeita responsabilidades; não mova arquivos apenas por estética.
3. **Correção.** Use quando a separação já é MVC e os findings são locais (segredo, API obsoleta, N+1). Corrija no lugar. Não crie camada para ficar igual ao diagrama.

Projeto com dois estilos de arquivo (parte em `src/`, parte na raiz) segue o estilo da maioria do código.

## Árvore Flask (greenfield)

```
<raiz-do-projeto>/
├── app.py                      # composition root
├── config/settings.py
├── models/
│   └── <entidade>_model.py
├── controllers/
│   └── <entidade>_controller.py
├── views/routes.py             # ou routes/<entidade>_routes.py
└── middlewares/error_handler.py
```

`app.py` só cria `Flask`, aplica config e CORS, registra rotas e, no `__main__`, chama `run` com host e porta vindos da config.

## Árvore Express (greenfield)

```
src/
├── app.js                      # composition root
├── config/settings.js
├── models/
│   ├── db.js
│   └── <entidade>Repository.js
├── controllers/
│   └── <entidade>Controller.js
├── views/routes.js
└── middlewares/errorHandler.js
```

Controller Express não chama `res` se a view já é quem envia. Preferência: controller devolve `{status, body}` e a rota envia. Se o projeto inteiro já usa `(req, res)` nos handlers, o modo evolutivo pode manter `res` na rota e deixar o controller puro.

## Modo evolutivo em Flask com SQLAlchemy

```
app.py                  # factory ou root, sem regra
config/settings.py      # URI, SECRET_KEY, DEBUG, porta
models/                 # os models atuais
controllers/            # casos de uso extraídos das rotas
routes/                 # Blueprint fino
middlewares/error_handler.py
services/               # só o que for integração externa (e-mail)
```

`Model.query.get(id)` vira `db.session.get(Model, id)`. O resto das queries ORM pode ficar nesta passagem se não for N+1 nem API da tabela obsoleta. Não migrar tudo para `select()` num único passo.

## Contrato HTTP

Antes de editar, grave uma lista interna:

```
METHOD PATH → status sucesso → chaves
METHOD PATH corpo inválido → status erro → chaves ou texto
```

Depois da refatoração, a lista é o teste.

Pode mudar:

- campo de resposta que contém senha, hash, segredo, PAN ou token fictício;
- proteção de rotas destrutivas ou administrativas apontadas por `AP-07`, que passam a exigir credencial (`401` sem credencial válida, `403` sem permissão ou chave inválida, mantendo `200` quando autorizadas);
- bloqueio de auto-promoção anônima de `role`/`tipo` privilegiado (`403`) e emissão de `token` assinado no `/login` quando necessário para `PB-12`;
- corpo de uma rota de SQL arbitrário, que passa a recusar a execução no formato de erro já usado pelo projeto;
- ordem de chaves JSON;
- mensagem de log.

Não pode mudar:

- método e caminho;
- status de sucesso (em chamadas autorizadas);
- chaves de sucesso que não sejam segredo;
- texto de erro que um cliente do repositório já compara, quando esse texto estiver em exemplo `.http` ou README do projeto;
- código de status dos erros de validação/negócio já cobertos por esse exemplo.

Não exija header obrigatório novo em rotas públicas de negócio. Headers de autorização (`Authorization: Bearer <token>` ou `X-Admin-Key`) são permitidos e obrigatórios exclusivamente nas rotas protegidas por `PB-12`.

## Configuração

Um módulo só:

- `PORT`, `HOST`, `DEBUG`, `DATABASE_URL` ou caminho do arquivo, `SECRET_KEY`, `ADMIN_API_KEY` (quando não houver fluxo de login), `TOKEN_MAX_AGE`, credenciais externas.
- Leitura com `os.environ` / `process.env`.
- `.env.example` com os nomes e valores vazios ou de desenvolvimento óbvios (`dev-only-change-me` para segredo local).
- Carregar `.env` se a dependência já estiver no projeto (`python-dotenv`, `dotenv`). Não adicionar pacote novo se der para ler o ambiente com a biblioteca padrão.
- Nenhum endpoint devolve valor de config sensível.
- `DEBUG` default falso. Ligue debug só se a variável de ambiente de debug da própria stack vier verdadeira.

O processo precisa subir com `python app.py` ou `npm start` sem variável obrigatória ausente: todo segredo tem fallback de desenvolvimento dentro do módulo de config, e em nenhum outro arquivo.

## Erro

Um handler. Formato igual ao que as rotas já usam (`{"erro": ...}` ou `{"error": ...}`). Exceção inesperada vira 500 com mensagem genérica. O detalhe fica no log do servidor, não no JSON.

## Validação da Fase 3

1. Instalar dependência se o import falhar.
2. Subir com o comando do README do projeto, na porta da config.
3. Para cada linha do contrato, uma requisição real. Salvar status recebido.
4. Para toda rota protegida por `PB-12`, validar os três cenários: sem credencial (`401`), credencial sem privilégio ou chave inválida (`403`) e chamada autorizada (`200`, ou `400` para SQL arbitrário recusado).
5. Rota de escrita que altera banco: usar o fluxo mínimo que o seed permite (criar e então ler, ou o `.http` do projeto).
6. Encerrar o processo ao terminar, para não deixar porta presa.
7. Se algo divergir do contrato, reverter a causa e repetir. O banner de completo espera todas as rotas originais.

Seed separado continua documentado e é executado antes do boot quando o README do projeto manda.
