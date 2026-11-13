# RELATÓRIO P2+P3 — WATCHDOG VRAM E PRELOAD 6000 (18/10/2026, 18:24–18:38)

## DECISÃO OBJETIVA

| Item | Decisão | Base |
|---|---|---|
| **P2 — Watchdog v2** | ✅ **APROVADO** | Implementado; **23/23 testes unitários** (transitório/persistente/crítico); rodou ao vivo durante o P3 **sem nenhum falso positivo** (0 eventos com pico de reservada 13,1 GB e driver 1,78 GB — abaixo dos limiares, corretamente silencioso); caminhos de abort validados em unidade (o teste ao vivo do abort real fica como validação opcional futura) |
| **P3 — Preload 6000** | ❌ **REPROVADO como otimização** (inconclusivo para ganho; custo real) | Difusão **681 s vs 683 s do T1 (−0,3%)**; passos-âncora **170/168/168/~174 s vs 174/169/168/169 s** — idênticos dentro do ruído; total 836,4 vs 846 s (−1,1%, vindo do áudio, 129 vs 137 s — variável confundida com strict e dentro do ruído). **Custo real medido**: +6,3 GB VRAM alocada (7.223 vs 76 MB), reservada 13.134 vs 8.814 MB, driver livre mínimo **1.779 vs 6.665 MB** |

**Conclusão prática:** manter `_preload_mb` FORA da configuração (a doc do próprio WanGP
antecipa: "Video steps are usually long enough to hide the transfers, so *Default* is
about as fast for videos" — os passos de vídeo de ~170 s escondem o streaming; preload
só ajudaria em passos curtos). Sem alteração de qualidade (mesmo seed/prompt; loudness
idêntico). **Nenhum ganho de velocidade é declarado** — a medição não sustenta um.

## 1. Preservação (Etapa 1) — verificada

- Backup: `LOGS\gen_test.py.pre_P2P3.backup` (SHA-256 inicial `D83B827C…`)
- Vídeo T1 confere com o manifesto (hash idêntico `789C1F70…`); eventos/telemetria T1 intactos
- Hashes pré-alteração registrados: gen_test.py `D83B827C…`, test1_settings `E4405F7C…`,
  wgp_config `7862EFD1…`
- O vídeo novo foi para `TESTE_01\teste_01_p3_preload.mp4` — **o vídeo aprovado do T1 não
  foi tocado** (diff de bytes confirma arquivos distintos, como esperado entre execuções)

## 2. Diffs aplicados (com rollback)

### P2 — `gen_test.py` (atual `F1A2E714…`; 11.916 → 18.652 bytes)
1. `WATCHDOG_LIMITS` + função pura `watchdog_decide()` (transitório warn → persistente
   abort; críticas imediatas: VRAM >15,5 GB e driver <50 MB; persistentes: VRAM >15 GB×3
   amostras, driver <300 MB×3, commit <5 GB×2) — **reservada NUNCA tratada como ocupada**:
   alocada, reservada, driver e commit registradas em colunas separadas no CSV
2. `MemorySampler.run()` usa a decisão pura; decisões (motivo+valores+timestamp+fase) em
   `<tag>_watchdog.jsonl` dedicado; abort grava marcador `…_ABORT_WATCHDOG.txt`
3. Laço de eventos: padrões HIP fatais (`hiperror`, `cudaerror`, `outofmemoryerror`,
   `device-sideassert`, `illegalmemoryaccess`, `invaliddevicefunction`, `hipruntimeerror`)
   em stream/erro → cancel + exit 4 imediato (sem esperar amostras)
- **Bugs capturados pelos testes ANTES de rodar** (motivo da exigência): `KeyError
  driver_hits` (mataria a thread do watchdog → geração sem proteção) e 2 checks de
  ordenação nos meus testes
- **Rollback:** copiar `LOGS\gen_test.py.pre_P2P3.backup` sobre `gen_test.py`

### P3 — `test1_p3_settings.json` (novo; settings de produção NÃO alteradas)
- Diff vs `test1_settings.json` verificado programaticamente: **exatamente 2 chaves** —
  `_preload_mb: 6000` (autorizado) e `output_filename: "teste_01_p3"` (preservação do
  vídeo aprovado). 13/15 chaves idênticas, prompt byte-idêntico, seed 7001, 6 passos,
  Spectrum 25%/0,08, 1152×640@24, GGUF Q4, Profile 5, euler, LoRA 1.0.
- **Rollback:** nenhum necessário (arquivo novo; production settings intactos).

### Diferença ambiental declarada ANTES de gerar (Etapa 4)
- T1 original rodou com `kernel_precision:"fast"`; o rerun com `"strict"` (fixado pela
  própria missão). Impacto medido na auditoria: difusão ±0 s; audio −1,7% (ruído).

## 3. Métricas do teste único (TESTE_01_P3, 18:24:52 → 18:38:40)

| Etapa | T1 (original) | P3 (preload) | Δ |
|---|---|---|---|
| Carga | 3 s | 3 s | = |
| Encode prompt | 10 s | 10 s | = |
| **Difusão (4 âncoras + 2 replays)** | **683 s** | **681 s** | −0,3% (ruído) |
| Passos âncora | 174/169/168/~169 | 170/168/168/~174 | idênticos (ruído) |
| Áudio estéreo | 137 s | 129 s | −5,8% (ruído/strict) |
| Save | 1 s | 2 s | = |
| **TOTAL** | **846 s** | **836,4 s** | **−1,1% (não conclusivo)** |

| Métrica | T1 | P3 | Δ |
|---|---|---|---|
| Vídeo | 10,125 s / 243 f / 8,27 MB / H.264 | idêntico | = |
| Loudness | −14,44 LUFS / TP −0,57 / LRA 20,5 | **idêntico** | = |
| Decode | sem erros | **sem erros** | = |
| VRAM alocada pico | 76 MB | **7.223 MB** | +6,3 GB (preload residente) |
| VRAM reservada pico | 8.814 MB | 13.134 MB | +4,3 GB |
| Driver livre mínimo | 6.665 MB | **1.779 MB** | −4,9 GB |
| Margem commit mínima | 22,8 GB | 13,3 GB | −9,5 GB (ainda ≥ 5 GB ✓) |
| Eventos do watchdog | — | **0** (silêncio correto) | ✓ |

## 4. Funcionamento real do watchdog (Etapa 5)

- **0 falsos positivos** durante toda a geração com preload (o cenário mais propenso a
  tocar limiares até agora: driver mínimo 1,78 GB).
- Log dedicado criado e fechado vazio: `TESTE_01_P3_watchdog.jsonl`.
- CSV completo com 165 amostras (alocada/reservada/driver/commit por timestamp).
- Limites ao vivo: reservada máx 13.134 MB (<15.360), driver mín 1.779 MB (>300),
  commit mín 13.326 MB (>5.120) — watchdog corretamente não interveio.
- **Validação pendente (opcional, requer nova autorização):** teste de abort real
  (ex.: preload 12.000 empurrando VRAM ao limite) — o único caminho não exercido ao vivo.

## 5. Artefatos preservados

`TESTE_01\teste_01_p3_preload.mp4` + `ANALISE_P3\` (frames/contato/meta) •
`LOGS\gen_test.py.pre_P2P3.backup` • `test_watchdog.py` (23 casos) •
`test1_p3_settings.json` • eventos/telemetria/watchdog do P3 no workspace (copiados ao
manifesto). Vídeo e métricas do T1 original: **intactos**.

## 6. Estado final recomendado

- **Watchdog v2: mantido** (protege todas as gerações futuras com as regras da missão).
- **Preload: não usar** em vídeos (sem ganho; consome 6,3 GB de VRAM que faltarão para
  janelas maiores). Settings de produção seguem sem `_preload_mb`.
- Nada mais foi alterado; P4 (Veda) e demais itens do plano seguem bloqueados sem nova
  autorização explícita.
