# Template do relatório

A Fase 2 grava um Markdown neste formato e imprime no chat só o resumo e a pergunta final. Não encurte finding. Não acrescente seção de refatoração: a Fase 3 ainda não aconteceu.

## Arquivo

```markdown
# ARCHITECTURE AUDIT REPORT

- Project: <pasta>
- Stack: <linguagem> + <framework e versão>
- Files: <N> analyzed | <linhas> lines
- Architecture: <classe da Fase 1>
- DB: <banco> | tables: <nomes>

## Summary

CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <título curto> — <AP-id>
- File: <caminho>:<linha> ou <caminho>:<linha-inicial>-<linha-final>
- Description: <o que o código faz, em uma ou duas frases>
- Evidence: `<trecho curto da linha>`
- Impact: <efeito em segurança, teste ou mudança>
- Recommendation: <ação objetiva>
- Playbook: <PB-id>

## Deprecated APIs

- <sinal> em <arquivo>:<linha> → <substituto>
- ou: Varredura AP-10 executada. Nenhuma API obsoleta do catálogo neste projeto.

## Confirmation

Fase 2 concluída. Nenhum arquivo de aplicação foi modificado.
Prosseguir com a refatoração (Fase 3)? [s/n]
```

## Regras de preenchimento

- Ordenação: CRITICAL, depois HIGH, depois MEDIUM, depois LOW.
- `File` usa caminho relativo à pasta do projeto, com barra `/`.
- Linha é a da evidência, não a do início do arquivo. Intervalo só quando o bloco inteiro é o finding (God module).
- `Evidence` é uma linha real, curta, entre crases. Não cole o arquivo.
- Vários pontos do mesmo finding: liste as linhas extras na Description, e deixe em `File` a âncora mais grave.
- A seção Deprecated APIs existe mesmo vazia.
- Contagens do Summary batem com o número de blocos `###`.

## Banner de console

Depois de gravar o arquivo, o chat mostra só isto, mais a lista dos títulos (sem repetir evidências):

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <pasta>
Stack:   <stack>
Files:   <N> analyzed | <linhas> lines
Report:  <caminho do arquivo>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings
- [CRITICAL] <título> — <arquivo>:<linha>
- [HIGH] <título> — <arquivo>:<linha>

================================
Total: <n> findings
================================
Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
```

## Banner da Fase 3

Só depois da validação passar. Árvore com os arquivos criados de verdade.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore>

## Validation
  ✓ Application boots without errors — <comando>
  ✓ Endpoints respond — <N>/<N>
  ✓ Intentional contract changes — <lista ou "nenhuma">
================================
```

Falha de validação não usa este banner. Diga qual comando falhou, qual rota e qual status veio.
