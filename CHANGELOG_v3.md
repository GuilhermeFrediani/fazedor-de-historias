# v3.0 — a camada que faltava: RENDERIZABILIDADE

## O diagnóstico em uma linha
O v2 ensinou a IA a **declarar** piada. O validador passou a contar declarações e
deu **8,5/10** para um episódio que na tela saiu como bug. O problema nunca foi
falta de piada no papel — foi **piada que um modelo de vídeo não consegue desenhar**.

## O que estava quebrado (e agora tem regra)

| # | Falha do v2 | Evidência no `arquivo.txt` | Correção na v3 |
|---|---|---|---|
| 1 | **Cadeia causal** (Rube Goldberg) | clipe #1: fio laça o eixo → fio recolhe → **reboca o carrinho** → comprime baldes → JUCA põe mais um balde. 4 efeitos em 10 s | **ORÇAMENTO DE FÍSICA**: 1 objeto + 1 causa + 1 efeito + 1 reação. Conector causal permitido: **1** |
| 2 | **Física irreproduzível** | "o fio recolhe e reboca o carrinho"; #5 "a curva varre as peças"; #29 "a tampa dispara pela rampa" | lista negra em código: corda/fio rebocando peso, objeto orbitando, balsa, objeto virando outro objeto, papel saltando para pasta |
| 3 | **Corpos parados** | #4 "JUCA waits at frame right"; #9 "TEO holds the planned lane"; #21 "TEO redirects his tape" | **REGRA DOS DOIS CORPOS**: os dois têm ação física em todo clipe; o segundo corpo **interfere** |
| 4 | **Reação proibida = riso zero** | Lei de Ferro nº 5: "NINGUÉM PERCEBE O ERRO" + "murmúrios zerados nesta leva" | reação **pequena e legível** + **1 som não-verbal obrigatório** por clipe (resfôlego, suspiro, estalo) |
| 5 | **Som pedido como imagem** | #15 e #25: `air duct hum drops into 1.2-second silence` no `overall_soundscape` | silêncio 1,2 s **banido como instrução visual**; pausa vira ação (objeto suspenso) |
| 6 | **Sem continuidade** | fumaça usou #1 #10 #15 #21 #25 #30 — clipes **não adjacentes** de um arco de 30 | **estado_in / estado_out** em todo clipe + estrutura 60 s = 6 clipes **consecutivos** |
| 7 | **Âncora engolindo a ação** | prompt final = estilo + set + estado + JUCA(1.900 c) + TEO(1.940 c) + ação | **ACTION primeiro**, âncoras **curtas** (~45 palavras cada), estilo/negativos no fim |
| 8 | **Nota fiscal × zero texto** | assinatura exige nota fiscal; Lei de Ferro nº 2 proíbe texto legível | nota existe como **objeto físico mudo** (folha em branco); a cena não depende de lê-la |
| 9 | **Validava o que não via** | `validar_dossie()` só olhava texto | `regras_v3.validar_renderizavel()` — 7 checagens de filmabilidade, peso 65% na nota |

## Arquivos novos
- **`regras_v3.py`** — `PROMPT_MESTRE_V3` (prompt de sistema), `montar_prompt_v3()` (ordem nova
  do prompt H3), `validar_renderizavel()` (o validador de física).
- **`PROMPT_SISTEMA_v3.txt`** — o mesmo prompt mestre solto, para colar em qualquer chat.
- **`fazedor_app/fumaca_v3.py`** — fumaça de 6 clipes **consecutivos** de OPERAÇÃO RALO EXATO
  reescrita sob as regras novas. Roda `--seco` para validar sem gastar GPU.
- **`fazedor_app/aplicar_v3.py`** — o patch aplicado no `fazedor_app.py` (idempotente, com asserts).
- **`CHECKLIST_QUALIDADE.md`** — 12 perguntas para julgar o MP4 antes de subir no YouTube.

## Arquivos alterados
- **`fazedor_app/fazedor_app.py`**
  - `instrucoes_dossie()` → devolve `regras_v3.PROMPT_MESTRE_V3`
  - `prompt_dossie()` → `regras_v3.montar_prompt_v3()` (ação primeiro; âncoras curtas)
  - `FORMATOS[6]` → `LIGACAO · CHEGADA · PRIMEIRA_FALHA · JEITINHO · ESCALADA · CLIMAX`
  - `validar_dossie` → vira casca: `_validar_dossie_v2` (forma+humor) + `validar_renderizavel`
  - nota final = `0,35 × humor + 0,65 × renderizabilidade`
  - backup automático em `fazedor_app.py.v2.bak`

## Campos novos no JSON do episódio
`estado_in`, `estado_out`, `fisica` (tombar|escorregar|quicar|transbordar|dobrar|inflar|rolar),
`reacao`. `beats` caiu de 3–4 para **2–3**. `action` caiu de 45–90 para **35–70 palavras**.

## Compatibilidade
Episódios v2 antigos continuam abrindo (os campos novos são opcionais na leitura), mas
**reprovam** na validação de renderizabilidade — que é exatamente o objetivo.
Para rodar a fumaça nova: `python fazedor_app/fumaca_v3.py --seco` e depois sem `--seco`.
