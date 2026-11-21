# Análise de projeto

Heurísticas da Fase 1. Preencha cada campo com evidência (arquivo). Se não achar, escreva "não identificado".

## 1. Raiz e manifests

A raiz do projeto é o diretório que contém um destes arquivos, o mais próximo do código pedido:

| Arquivo | Linguagem provável |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python |
| `package.json` | JavaScript ou TypeScript |
| `go.mod` | Go |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java ou Kotlin |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.csproj`, `*.sln` | C# |

Mais de um manifest: o da pasta pedida pelo usuário ganha. Não misture dois serviços no mesmo banner.

## 2. Linguagem

Conte arquivos de código por extensão (`.py`, `.js`, `.ts`, `.go`, `.java`, `.php`, `.rb`, `.cs`). A linguagem da Fase 1 é a de maior contagem dentro da raiz, fora de pastas ignoradas.

Arquivo de tipos ao lado de JavaScript (`.ts` presente, ou `"typescript"` em `devDependencies`) muda o rótulo para TypeScript.

## 3. Framework e versão

Leia o manifest. Não chute a versão "latest".

| Sinal no manifest ou no import | Framework |
|---|---|
| `flask` em requirements ou `from flask import` | Flask |
| `django` ou `manage.py` | Django |
| `fastapi` ou `from fastapi import` | FastAPI |
| `"express"` em dependencies ou `require('express')` / `from 'express'` | Express |
| `@nestjs/core` | NestJS |
| `fastify` | Fastify |
| `gin` no `go.mod` ou `github.com/gin-gonic/gin` | Gin |
| `spring-boot` no pom ou gradle | Spring Boot |
| `laravel/framework` | Laravel |

Versão: o spec exato quando estiver pinado (`flask==3.1.1`). Quando for range (`^4.18.2`), registre o range e a versão instalada só se `node_modules` ou o lock file mostrar a versão resolvida. Não abra `node_modules` inteiro: use `package-lock.json` na chave `node_modules/<pacote>.version`, ou deixe o range.

Dependências: liste os pacotes de runtime ligados a HTTP, ORM, banco, auth e CORS. Marque pacote declarado e não importado em lugar nenhum como dependência ociosa (isso vira finding na Fase 2, não no banner).

## 4. Entrypoint

Procure nesta ordem:

1. Script `start` ou `dev` do `package.json`.
2. Bloco `if __name__ == "__main__"` ou `app.run(`.
3. `main` em `go`, `public static void main`, `artisan`.
4. Arquivo citado no README do próprio projeto.

Registre host e porta a partir da chamada de listen (`app.run`, `app.listen`, `PORT`). Default de framework só se o código não fixar a porta: Flask 5000, Express não tem porta sem `listen`.

## 5. Banco e tabelas

| Sinal | Banco |
|---|---|
| `sqlite3`, `better-sqlite3`, arquivo `.db`, `sqlite:///` | SQLite |
| `:memory:` na conexão | SQLite em memória |
| `psycopg`, `pg`, `postgres://` | PostgreSQL |
| `mysql2`, `pymysql`, `mysql://` | MySQL |
| `mongodb`, `mongoose` | MongoDB |
| `SQLAlchemy(`, `flask_sqlalchemy` | ORM SQLAlchemy sobre a URI lida em `SQLALCHEMY_DATABASE_URI` |

Tabelas: nomes em `CREATE TABLE`, `__tablename__`, ou `db.Model` com `__tablename__`. Não invente tabela a partir de um substantivo de rota se o DDL não existir.

Seed: arquivo `seed`, `executemany` de insert, ou `INSERT INTO` no boot. Diga se o seed é automático no boot ou se exige comando separado.

## 6. Arquitetura atual

Classifique com uma destas três, e justifique com a árvore:

| Classe | Critério |
|---|---|
| Monolítica | HTTP, regra de negócio e acesso a dados convivem nos mesmos poucos arquivos. Não há pacote de domínio. |
| Camadas parciais | Existem pastas como `models/`, `routes/`, `services/`, `utils/`, mas a rota ainda faz ORM, validação e regra, ou não existe controller. |
| MVC | Rota só encaminha, controller orquestra, model só persiste ou representa entidade, config isolada, erro centralizado. |

Conte arquivos de código analisados (os que você abriu ou que entram na contagem de linguagem). Não conte a skill, o README, `.http` de exemplo, lock file.

Domínio: substantivos das rotas e das tabelas (`/clientes`, `faturas`). Uma frase, não um parágrafo.

## 7. Banner obrigatório

Imprima exatamente esta estrutura, com os valores desta execução:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework e versão ou range>
Dependencies:  <lista curta>
Domain:        <uma frase>
Architecture:  <Monolítica | Camadas parciais | MVC> — <uma frase>
Source files:  <N> files analyzed
DB:            <banco> | tables: <nomes ou "não identificado">
Entry:         <arquivo:linha> | <host>:<porta>
================================
```

## 8. O que não fazer na Fase 1

- Não listar anti-patterns ainda. Isso é a Fase 2.
- Não estimar "uns 800 linhas". Conte.
- Não tratar `routes/` existente como prova de MVC.
- Não tratar ausência de pasta `views/` como defeito antes da auditoria. A Fase 1 descreve o que é, não o que deveria ser.
