---
name: refactor-arch
description: >-
  Analisa um backend legado, audita anti-patterns de MVC, SOLID, segurança e
  APIs obsoletas com arquivo e linha, e refatora para MVC só depois de
  confirmação humana, validando boot e endpoints. Use quando o usuário
  invocar refactor-arch, pedir auditoria arquitetural, code smells,
  anti-patterns ou refatoração para MVC em Flask, Express ou outro backend.
disable-model-invocation: true
---

# refactor-arch

Skill de auditoria e refatoração para MVC. Agnóstica de linguagem. Três fases, nesta ordem. O contrato HTTP público sai do código antes de qualquer edição e continua respondendo depois.

## Barra de qualidade

- Finding sem arquivo e linha não entra no relatório.
- Busca textual é pista. A linha lida confirma o finding.
- "Código ruim", "melhorar arquitetura" ou severidade sem evidência são proibidos.
- A escala de severidade é a do catálogo: CRITICAL, HIGH, MEDIUM, LOW. Não promova um item porque ele é feio.
- Não invente framework, versão, tabela ou endpoint. Se o arquivo não diz, registre "não identificado".
- Não declare sucesso sem ter subido a aplicação e chamado os endpoints originais nesta sessão.

## Fases e leituras

Leia só o material da fase atual. Os links são de um nível.

| Fase | Ler | Pode editar código da aplicação? |
|---|---|---|
| 1 Análise | [analise-de-projeto.md](analise-de-projeto.md) | Não |
| 2 Auditoria | [catalogo-anti-patterns.md](catalogo-anti-patterns.md) e [template-relatorio.md](template-relatorio.md) | Não. O único arquivo novo é o relatório |
| 3 Refatoração | [guidelines-mvc.md](guidelines-mvc.md) e [playbook-refatoracao.md](playbook-refatoracao.md) | Sim, somente depois do sim humano |

Checklist desta execução:

```
- [ ] Fase 1 — banner impresso no chat
- [ ] Fase 2 — relatório gravado em reports/
- [ ] Confirmação humana explícita recebida
- [ ] Fase 3 — MVC aplicado segundo o modo de migração
- [ ] Boot sem erro
- [ ] Endpoints originais respondem
```

## Onde gravar o relatório

A skill não conhece nomes de pasta deste ou de outro repositório.

1. A raiz do projeto é o diretório do código pedido, aquele do manifest mais próximo (`requirements.txt`, `package.json` ou o equivalente da linguagem).
2. A raiz do repositório é o ancestral mais próximo dessa pasta que contém `.git`. Sem `.git`, a raiz do repositório é a raiz do projeto.
3. Se o usuário informar um caminho de relatório, use esse caminho.
4. Sem caminho informado, grave em `<raiz-do-repositório>/reports/audit-<nome-da-pasta-do-projeto>.md`.

Um projeto por execução. Se o diretório pedido tiver mais de um manifest de aplicação, pergunte qual auditar. Não misture findings de projetos diferentes no mesmo relatório.

## Fase 1 — Análise

1. Leia [analise-de-projeto.md](analise-de-projeto.md) e aplique as heurísticas no projeto escolhido.
2. Ignore `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.git` e a própria pasta da skill.
3. Imprima no chat o banner da Fase 1, com os campos lidos nesta execução. Não reaproveite banner de exemplo.
4. Pare. Não proponha patch ainda.

## Fase 2 — Auditoria

1. Leia o catálogo e o template.
2. Percorra o código de produção e marque cada anti-pattern cuja evidência estiver na linha. Inclua a passagem de APIs obsoletas mesmo que o resultado seja "nenhuma".
3. Ordene CRITICAL, HIGH, MEDIUM, LOW. Dentro da mesma severidade, segurança antes de estilo.
4. Grave o relatório no caminho resolvido acima, no formato do template.
5. Imprima no chat o resumo (contagens) e o caminho do arquivo.
6. Pare e pergunte, nesta forma:

```
Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
```

Aceite apenas `s`, `sim`, `y` ou `yes` como autorização. Qualquer outra resposta encerra sem editar código. Não antecipe a Fase 3 no mesmo turno da pergunta.

## Fase 3 — Refatoração

Só comece com autorização explícita dada depois do relatório.

1. Leia as guidelines e o playbook.
2. Escolha o modo de migração (greenfield, evolutivo ou só correção). Projeto que já tem `models/` e `routes/` usa o modo evolutivo. Não desmonte uma separação que já existe para recriar outra igual.
3. Inventarie o contrato: método, caminho, status de sucesso, status de erro e chaves do JSON. Salve essa lista antes da primeira edição.
4. Aplique os padrões do playbook ligados aos findings. Não refatore achado que não está no relatório.
5. Configuração sensível sai do código espalhado e vai para um módulo de config lido de variável de ambiente. O boot local precisa continuar possível: documente as variáveis em `.env.example` e use fallback só de desenvolvimento, num único lugar, nunca devolvido em JSON.
6. Valide de verdade:
   - instale dependências se faltarem;
   - suba o processo e registre host e porta lidos do código;
   - chame cada rota inventariada, inclusive o caminho de erro fácil (recurso inexistente ou corpo vazio);
   - se o boot ou uma rota quebrar, corrija e repita. Não siga para o banner de sucesso.
7. Imprima o banner da Fase 3 com a árvore real e o resultado de cada checagem.

## Regras da Fase 3 que não se negociam

- Caminho, método e status de sucesso dos endpoints originais permanecem.
- Chaves de JSON de sucesso permanecem. Remover campo que vaza senha, segredo, cartão ou token é mudança intencional: registre no log de validação.
- Não crie autenticação nova que faça as chamadas atuais, feitas sem credencial, passarem a responder 401. Achado de "falta auth" fica no relatório. A exceção é execução de SQL enviado pelo cliente: a rota permanece, a execução arbitrária acaba, a resposta de recusa usa o formato de erro que o projeto já tinha.
- Login com a mesma senha dos dados de exemplo continua funcionando depois de trocar o armazenamento por hash.
- Não troque de banco, não adicione framework e não renomeie o domínio.
- Idioma das mensagens já existentes permanece.
