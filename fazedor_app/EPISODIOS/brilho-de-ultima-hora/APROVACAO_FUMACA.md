# Aprovação da Fumaça de 60 s — 2026-11-25

**Veredito do usuário:** "Está muito bom, posso prosseguir para produção."
**Data da aprovação:** 25/11/2026 (assistiu ao `brilho-de-ultima-hora_SMOKE60.mp4` no painel do OpenCode).

## Entregável aprovado

| Item | Valor |
|---|---|
| Arquivo | `brilho-de-ultima-hora_SMOKE60.mp4` |
| Duração | 61,8 s (6 clipes × 10,2 s, montagem `--cortar-meio`) |
| Tamanho | 31,8 MB |
| Áudio | média -25,2 dB / pico -1,7 dB |
| Cópia | Área de Trabalho + `EPISODIOS/brilho-de-ultima-hora/` |
| Commit | `a64df8e` (final + c06), clipes em `clipes_smoke/` |

## O que a fumaça validou

- **Gerador de história + prompts**: "Brilho de Última Hora" com 6 settings (steps 8, 10 s), 8 objetos no registro, arco do mesmo objeto.
- **Cadeia de render + gate**: âncora única, estado real por clipe, gate de 5 frames, scan de céu, montagem automática.
- **Set fechado (lição v7 confirmada)**: a janela em arco foi **removida** (arco cego) e o céu desapareceu de todos os clipes. O problema de 3 h era uma frase contraditória no fim do prompt ("plain and clear") + a janela na âncora.

## Correções de pipeline feitas nesta rodada (todas commitadas)

| Commit | Correção |
|---|---|
| `987ca1b` | vidro "plain and clear" → leitoso opaco no fim do prompt |
| `57402a5` | janela em arco → **arco cego** de pedra (determinístico) |
| `979596e` | cadeia não morre se a âncora do banco foi apagada |
| `fbdbd95` | cortina fechada flush na parede + `TENT_MAX=1` (time-box) |
| `e388978` | graduação de régua/trena é **diegética** (não é texto) |
| `c17222f` | prop em posição oculta (atrás da cortina/bolso) não conta como ausente |

## Ressalvas conhecidas (cosméticas, aceitas pelo usuário)

- c01: no último frame TÉO segura a nota aberta em vez da régua.
- c02/c03/c04: "texto" nos planos do metro dobrável (regra nova já isenta graduação).
- c05: metro na prateleira direita em vez da esquerda.
- c06: a haste metálica do mop some no fim (o rod é registrado como "suporte lateral" em c3-c6).
- c06: o QC episódico marcou "homem de verde atrás da pia" como extra — **é o cliente autorizado** (`cliente=SIM` no c06), o aperto de mão final é o payoff; o flag `cliente` não chegou na passada episódica do QC.

## Pendências herdadas

- 60 s do **"Operação Ralo Exato"**: 20 s aprovados; faltam c05/c06 e re-render de c03/c04 com a porta de aço.
- Face blur pós-render (H3 inpaint/2K) — não implementado.
