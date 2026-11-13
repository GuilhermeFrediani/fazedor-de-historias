# PLANO DE OTIMIZAÇÃO — MINIMAX H3 (18/10/2026, pós-auditoria)

**Princípios:** preservar o nível visual/sonoro dos Testes 1/2; corrigir a continuidade
semântica do Teste 3 via prompt (não via memória); só aceitar mudanças com melhoria
demonstrável. **Exclusões (suas regras):** SageAttention (mais lento na sua medição
antiga), 3 passos (perda de nitidez/artefatos relatada), "image_start" (proibido).
**Nada abaixo foi executado — tudo aguarda autorização.**

## 1. ESTIMATIVA PARA 5 MINUTOS (300 s ≈ 7.200 frames)

Base medida: C(W)=0,2508·W+0,001839·W² s/passo-âncora (erro ≤1% nos 3 testes);
4 âncoras + 2 replays Spectrum por janela; janelas 362 frames / 344 novas / overlap 18;
áudio 11,7 s/s; overheads por janela ~72 s; modelo reproduz T1/T2/T3 com erro ≤1%.

| Componente | Medido? | Conservador | Mediano | Otimista |
|---|---|---|---|---|
| Difusão (21 janelas: 1×362 + 19×362 + 1×320) | medido+extrapolado | 27.615 s | −20% → 22.092 s | −45% → 15.188 s |
| Áudio (11,7 s/s × 300 s) | medido | 3.510 s | 3.510 s | 3.510 s |
| Overheads (encode/VAE/save por janela) | medido | ~1.480 s | ~1.480 s | ~1.480 s |
| Carga + extras | medido | ~50 s | ~50 s | ~50 s |
| **TOTAL** | | **~9,1 h** | **~7,5 h** | **~5,6 h** |

- **Conservador** = modelo medido sem nenhuma otimização — **acima da sua janela de 6–8 h**.
- **Mediano** = difusão −20% via Veda Sparse (claim do changelog, NÃO medido nesta GPU).
- **Otimista** = difusão −45% (Veda "até 2× em vídeos longos" no melhor caso + micro-ganhos).
- Marcado como extrapolado: a estrutura de 21 janelas (só 2 emendas foram testadas);
  sustentação da margem de commit ao longo de horas; deriva de consistência após muitas
  emendas. **Três testes curtos não validam 5 minutos** — a etapa intermediária de 30–60 s
  é obrigatória antes do compromisso.

## 2. MUDANÇAS PROPOSTAS (ordenadas por ganho/risco/custo)

### P1 — Corrigir a cena do Teste 3 (QUALIDADE — prioridade do usuário)
- **O quê:** regenerar o T3 com prompt reestruturado (mesma seed/config): remover o
  conflito pia-origem/planta-destino ("she lifts the watering can that already stands
  beside the sink" em vez de encher na pia) e ancorar o destino da água ("tilts the can
  so a thin stream falls onto the dark soil of the small green plant on the windowsill");
  manter cadeia ≤8 ações.
- **Ganho:** corrige (a) muda no bico e (b) regar a pia (erros semânticos localizados na
  janela 1 — evidência: Fase 4 da auditoria).
- **Risco de qualidade:** nenhum (só prompt). **Custo:** 1 geração T3 (~31 min) + análise.
- **Rollback:** nenhum necessário (prompt é entrada; T3 atual preservado).
- **Critério de aceite:** você confere os frames da ação (frames_acao_rega) e a emenda.

### P2 — Watchdog de VRAM v2 (SEGURANÇA — pré-requisito das demais)
- **O quê:** aplicar o diff de WATCHDOG_VRAM_PROPOSTA.md (só `gen_test.py`, arquivo nosso).
- **Ganho:** enforcement real das regras da missão (VRAM/driver/HIP) sem abortos falsos.
- **Risco:** nenhum à qualidade; risco de falso-positivo mitigado pela persistência K=3.
- **Custo:** aplicação 5 min + validação em 1 rerun T1 (~14 min, já serve de baseline p/ P3).
- **Rollback:** restaurar `gen_test.py` atual (backup antes da aplicação).

### P3 — Preload 6000 (VELOCIDADE — barato, seguro, hipótese medida a testar)
- **O quê:** rerun do Teste 1 com `_preload_mb: 6000` (viável agora: commit 47 GB; era
  impossível com 18 GB — foi por isso que removemos).
- **Ganho hipotético:** reduzir stalls de streaming de blocos por passo (0–15%?) —
  **hipótese**; seu ambiente antigo usava 6000, mas sem tempos absolutos antigos não
  há comparação possível.
- **Risco de qualidade:** nenhum esperado (mesmos pesos). **Risco memória:** VRAM
  reservada sobe ~6 GB → com watchdog v2 ativo, limites protegidos; se ultrapassar,
  o teste aborta com segurança.
- **Custo:** 1 geração T1 (~14 min) comparando s/passo (baseline 170 s medido).
- **Rollback:** `_preload_mb` removido do settings (1 linha).
- **Aceite:** s/passo ≤ baseline com margem ≥ segurança; vídeo comparável (seed 7001).

### P4 — Veda Sparse 20B (VELOCIDADE — maior ganho potencial)
- **O quê:** testar `minimax_h3_fl2va_pruned_veda` (atenção esparsa aprendida; changelog:
  "at least 20% faster, even more on larger/longer videos; same settings and LoRAs").
- **Ganho potencial:** 20% a 2× na difusão = 1,5 a 3 h num vídeo de 5 min. **Claim do
  fabricante — não medido nesta GPU.**
- **Risco de qualidade:** desconhecido (validar visualmente vs T1/T2 mesmo seed);
  possivelmente mais VRAM ("a bit more VRAM" — changelog).
- **Custo:** download do checkpoint Veda (~20 GB) + 1 rerun T1 comparativo (~14 min+) +
  sua avaliação visual/sonora lado a lado.
- **Rollback:** voltar o settings para `minimax_h3_fl2va_pruned` (1 linha; arquivos do
  modelo permanecem no disco).
- **Aceite:** s/passo ≥20% menor, E qualidade aprovada por você no mesmo seed/prompt.

### P5 — Encoder Quanto INT8 (VELOCIDADE — ganho menor)
- **O quê:** testar `config: "int8"` no encoder (arquivo de 26,7 GB já baixado) em vez do
  GGUF Q4. Dados noturnos de velocidade INT8 eram inválidos (thrashing sem pagefile);
  os dois agora precisam de medição limpa.
- **Ganho:** encode 10–40 s → ~4–12 s por janela (~1–2% do total) — **pequeno**.
- **Risco de qualidade:** mesmo texto→tokens (mesma família); nenhum esperado.
- **Custo:** 1 teste curto. **Rollback:** `config: "gguf_q4_k_m"` (1 linha).
- **Nota:** só vale se P4/P3 não forem suficientes; prioridade baixa.

### P6 — Investigar pipeline de áudio (VELOCIDADE — custo alto)
- **O quê:** o decode de áudio é serial por janela (11,7 s/s → ~58 min num vídeo de 5 min,
  6% do total). Investigar no código se é GPU/CPU e se é adiapável/paralelizável.
- **Risco:** mexer em código de terceiros — exigiria patch documentado + sua aprovação.
- **Prioridade:** baixa (ganho ≤6% do total; custo de validação alto).

### P7 — Overlap de janela (VELOCIDADE — risco de continuidade)
- **O quê:** reduzir `sliding_window_overlap` (18) reduziria ~17% do trabalho das janelas
  2+. **NÃO recomendado agora:** o overlap é o mecanismo da emenda que o T3 validou;
  mexer nele antes de validar 30–60 s troca duas variáveis ao mesmo tempo.
- **Custo/risco:** alto risco de degradação de continuidade. Manter congelado.

### NÃO PROPOSTAS (por suas regras): SageAttention; 3 passos; image_start;
WGPKernels-AMD (kernel "unvalidated on AMD" segundo a doc oficial — só entrar com
evidência forte de ganho e sua autorização explícita).

## 3. SEQUÊNCIA RECOMENDADA DE VALIDAÇÃO (com autorizações)

1. **P2+P3 juntos num rerun do T1** (31 min totais): aplica watchdog v2 + preload 6000 →
   mede s/passo vs baseline 170 s → valida os dois com um único vídeo.
2. **P1** (rerun T3 com prompt corrigido, ~31 min): sua aprovação visual da nova cena +
   emenda (usa o que P2 protegeu).
3. **Etapa 30–60 s** (sem ela, não atacar 5 min): 1 geração de 60 s (~1 h) mede margem
   de commit/VRAM ao longo de ~7 janelas + deriva de consistência.
4. **P4 Veda** (se o passo 1 não alcançar a meta): download + comparativo lado a lado.
5. **RIFE ×2 e upscale:** medição independente APÓS um vídeo nativo aprovado
   (post-processing; não afeta os tempos acima).

## 4. RESUMO EXECUTIVO

- **Sem otimizações, 5 minutos ≈ 9,1 h (medido/extrapolado) — acima da sua janela de 6–8 h.**
- Spectrum JÁ economiza 33% (4 âncoras em 6 passos — confirmado idêntico ao antigo).
- Sem reprocessamento de janelas (hipótese refutada) — a estrutura de janelas é eficiente.
- Maiores alavancas: Veda Sparse (fabricante promete 20–2×; validar) e preload
  (barato de testar); áudio/encoder são ganhos marginais; overlap fica congelado.
- O defeito do T3 é semântico (prompt) — corrigível sem tocar em memória/config.
