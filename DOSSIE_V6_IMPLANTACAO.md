# DOSSIÊ DE IMPLANTAÇÃO — PROMPT_MESTRE_V6

**Data:** 26/11/2026
**Escopo:** reconstrução da inteligência que escreve os episódios, sem alterar o contrato que o MiniMax H3 consome.
**Execução:** nenhum teste de fumaça, nenhuma chamada de API, nenhuma geração de vídeo. Apenas aplicação de código/prompt e verificação estática.

---

## 1. Resultado da verificação

```
64/64 verificações estáticas PASS · 0 FAIL
COMPILE OK · teste_canon EXIT 0 · teste_v6 EXIT 0 · teste_auditor EXIT 0 · benchmark --dry EXIT 0
```

O contrato do render permanece exatamente o mesmo:
`integrated_multimodal_description:` + `overall_soundscape:` + `non_diegetic_music:`,
montado por `regras_v4.montar_prompt_v4()` e consumido por `gen_test.py`.

---

## 2. O que mudou na cadeia de prompt (antes → depois)

| Ponto | Antes | Depois |
|---|---|---|
| System do criador | `PROMPT_MESTRE_V5` (v4 + cérebro injetado), com regras repetidas e contraditórias | `PROMPT_MESTRE_V6` (14 partes, hierarquia explícita, 5 fases de produção) |
| Mensagem de lapidação (UI) | "RESPONDA … no TEMPLATE DE SAÍDA da **MEMORY DIRECTIVE**" (beats + action) | "formato **PROMPT_MESTRE_V6** (planos/estado/som/música — sem beats e sem action)" |
| Correção com IA | system = `PIECES.sistema` (prompt legado v2 de 14 regras) + cérebro V5 | system = `PIECES.v6`, sem duplicar cérebro |
| Pacote p/ chat externo (modo cola) | MEMORY DIRECTIVE + exemplo legado de 13 clipes | `PROMPT_MESTRE_V6`; MEMORY DIRECTIVE só como fallback |
| Bloco `=== TAREFA ===` (AgentRouter) | "o episódio tem **30 clipes**" fixo, sem citar o contrato | cita V6, quantidade definida pelo pedido (3/6/30 — "não assuma 30 por padrão") |
| Regras de áudio no cérebro | "ZERO … música"; `non_diegetic_music = N/A` | música instrumental discreta sempre presente + som bucal não-verbal obrigatório |
| Validador de música | exigia `N/A` e a seguir escondia o erro quando havia `planos` | exige texto instrumental; vazio/`N/A`/vocal = erro |
| Barreira de produção | `gerar_settings()` criava settings mesmo com episódio reprovado | valida antes e aborta; `exigir_cortes=True` barra clipe com 1 plano |

---

## 3. Arquivos criados

| Arquivo | Papel |
|---|---|
| `fazedor_app/regras_v6.py` | Fonte canônica do `PROMPT_MESTRE_V6` (25.686 chars, 14 partes) |
| `PROMPT_SISTEMA_v6.txt` | Versão idêntica para colar em qualquer IA (byte a byte igual ao módulo) |
| `fazedor_app/auditor_v6.py` | `PROMPT_AUDITOR_V6` (6.743 chars) + `mensagem_usuario(ep, ledger)` |
| `fazedor_app/benchmark_v6.py` | Benchmark Astra × Sol: 5 tarefas + 4 defeitos plantados + auditoria cruzada |
| `MEMORY_DIRECTIVE_v1.0_extraida_do_dossie.txt` | Cópia verbatim da seção 12 do `.docx` (referência/fallback) |

---

## 4. Arquivos alterados

| Arquivo | Mudanças (linhas atuais) |
|---|---|
| `fazedor_app/fazedor_app.py` | import de `regras_v6` (:42) e `auditor_v6`; `instrucoes_dossie()` → V6 (:439); barreira em `gerar_settings()` (:795) com `exigir_cortes=True` (:819); `=== TAREFA ===` (:905); rota `/api/auditar` (:1148); `/api/pieces` expõe `v6` (:1178); método `_auditar()` (:1223); validador de música (:673); fim da supressão do erro de música (:1316) |
| `fazedor_app/ui.html` | `PIECES.v6` (:242); botão do auditor (:200) e `<pre>` do relatório (:207); modo cola usa V6 (:510); mensagem de lapidação (:649); correção com sistema V6 (:693); handler do auditor (:836-851) |
| `fazedor_app/regras_v4.py` | LEI DO SOM e FORMATO DA SAÍDA sem `N/A`; `montar_prompt_v4(..., exigir_cortes=False)` com erro para <2 planos |
| `fazedor_app/canon_comedia.py` | regra de áudio V6 no cérebro (:211), no CHECKLIST (:300) e no `BLOCO_CURTO` (:334) |
| `fazedor_app/certificar_agentrouter.py`, `testar_autoepisodio.py`, `teste_autoepisodio_60s.py` | mensagens de usuário em formato V6 e preferência por `v6` |
| `README.md` | linhas da V6, do auditor e do benchmark |

---

## 5. Correções de compatibilidade aplicadas (V6 × código real)

1. **Som de boca vs "sem voz"** — o validador exige `snort/sigh/breath/grunt/huff/puff/whistle/tongue/nasal/swallow` por clipe. A V6 proibia "sons vocais" de forma ambígua; agora distingue: fala proibida, som bucal não-verbal obrigatório.
2. **Escalada** — a V6 propunha "superfície/estrutura" e dizia que a ordem não era obrigatória; o Python exige `objeto → parede → piso → teto` em ordem não-decrescente (1 degrau em ≤6 clipes; 3 em 30). A V6 foi reescrita com o vocabulário fechado.
3. **`canon` literal** — o validador rejeita qualquer valor diferente de `zeca_joca_v1`; a V6 agora imprime essa string literalmente.
4. **`planos[1]` como `action` legado** — descoberto na verificação: o checador v3 deriva `action` do plano do meio e exige 20–95 palavras com TEO **e** JUCA. Escrito nos artigos 25 e 51 da V6.
5. **Fallback de 1 plano** — `exigir_cortes=True` no caminho de settings + barreira de validação em `gerar_settings()` (`forcar=True` como saída de emergência).

---

## 6. Correções de mensagem aplicadas (o que faltava)

O system já era V6, mas as mensagens ao redor ainda pediam o formato antigo — contradição direta. Corrigido:

1. Lapidação: TEMPLATE DA MEMORY DIRECTIVE → formato V6.
2. Correção com IA: prompt v2 → V6.
3. Modo cola: MEMORY DIRECTIVE + exemplo legado → V6.
4. `=== TAREFA ===`: "30 clipes" fixo → quantidade pedida e contrato V6.
5. Harnesses: mesma mensagem antiga → formato V6.

A MEMORY DIRECTIVE continua no código (`memory_directive()` e `/api/pieces`) apenas como fallback e referência histórica.

---

## 7. AUDITOR_V6

- Não cria episódio; recebe JSON + `STATE_LEDGER` e aplica 7 etapas (A–G).
- Notas com pesos 10/10/15/25/25/15; 4 níveis de severidade; correção localizada com campos dependentes.
- Saída travada no contrato `auditoria / problemas / correcoes / resumo`.
- `/api/auditar` escolhe **o outro modelo** por padrão (`modelo_criador` → oposto em `AR_MODELOS`); `mesmo_modelo: true` força o mesmo; não passa por `reforcar_canon()`; rejeita relatório inválido.
- UI: botão na seção 5 + relatório em `<pre>`.

---

## 8. Benchmark

`python benchmark_v6.py` (padrão, seco) · `python benchmark_v6.py --run` (chama as APIs).
Cinco tarefas idênticas por modelo, quatro defeitos plantados, auditoria cruzada, pesos 25/25/25/15/10, saída em `BENCHMARK_V6_RESULTADO.json`. **Não executado** — o `--run` consome várias gerações longas.

---

## 9. O que NÃO foi feito (limites reais)

- **Nenhuma validação com modelo real** — eficácia da V6 e a escolha Astra/Sol seguem não mensuradas.
- **Nenhum teste de fumaça / render** (pedido explícito).
- **Produção de 90–102 clipes não habilitada**: `FORMATOS` aceita só 3, 6 e 30; a V6 avisa isso, mas o código ainda não tem o formato longo.
- **Documentação legada**: `README_FAZEDOR.md` e os exemplos `exemplo_episodio_*.json` ainda descrevem o fluxo v1/v2. Não afetam a execução (a V6 não usa o exemplo antigo).
- **`teste_fazedor.py` falha por motivos pré-existentes**: usa o exemplo de 13 clipes (fora dos formatos) e procura `SpeechRecognition` numa UI que não contém essa string. Não foi alterado.

---

## 10. Rollback

1. Em `fazedor_app.py:439`, trocar `return regras_v6.PROMPT_MESTRE_V6` por `return regras_v4.PROMPT_MESTRE_V5`.
2. Se `regras_v6.py` for removido, `instrucoes_dossie()` cai sozinho na V5 e a UI cai para `dossie_md`/`sistema`.
3. Os patches do validador (música, cérebro, barreira) são independentes e podem ser revertidos separadamente — mas revertê-los **sem** trocar o prompt reintroduz a contradição de áudio.
