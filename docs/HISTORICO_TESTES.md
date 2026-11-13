# HISTÓRICO DE TESTES — FASES C/D (TESTES DE VÍDEO)

**ATUALIZAÇÃO 18/10/2026 (sessão de recuperação): OS 3 TESTES FORAM CONCLUÍDOS**
- Teste 1: ver TESTE_01\RELATORIO_TESTE_01.md (10,125 s; 846 s de geração; margem mín. 22,8 GB)
- Teste 2: ver TESTE_02\RELATORIO_TESTE_02.md (12,25 s; 1.109,6 s; margem mín. 17,3 GB; corte
  de câmera + narrativa completa processada em janela única)
- Teste 3: ver TESTE_03\RELATORIO_TESTE_03.md (18,79 s; 1.866,2 s no retry; **2 janelas com
  emenda validada**; margem mín. 9,3 GB) — 1ª tentativa falhou por bug de dispatch AMD
  (kernel CUTLASS CUDA-only no VAE encode do overlap; diagnóstico e correção
  `kernel_precision:"strict"` em TESTE_03\RELATORIO_TESTE_03_TENTATIVA1_FALHA.md e PATCHES_DIFF.md)
- O bloqueio noturno foi resolvido pelo pagefile fixo de 32 GB (limite de commit
  18,04 → 47,16 GB medidos), aplicado com autorização do usuário.

## COMPARAÇÃO DOS TRÊS TESTES (mesma config/seed 7001)

| Métrica | Teste 1 | Teste 2 | Teste 3 (retry) |
|---|---|---|---|
| Duração do vídeo | 10,125 s | 12,25 s | 18,79 s |
| Frames | 243 | 294 | 451 |
| Janelas de difusão | 1 | 1 | **2 (overlap 18)** |
| Tempo total de geração | 846 s | 1.109,6 s | 1.866,2 s |
| s de geração por s de vídeo | 83,6 | 90,6 | 99,3 |
| Encode do prompt | 9,9 s | 10,5 s | 11,4 s (j1) |
| Margem de commit mínima | 22,8 GB | 17,3 GB | 9,3 GB |
| VRAM reservada pico | 8,8 GB | 9,2 GB | 16,05 GB (1 amostra, VAE encode j2) |
| Driver livre mínimo | 6,7 GB | 6,3 GB | 0 MB (1 amostra, idem) |
| Loudness integrado | -14,44 LUFS | -17,96 LUFS | -24,38 LUFS |
| Fala pt-BR | janela 2,83–4,95 s | janela 4,38–10,99 s | janela ~15,05–17,76 s |
| Integridade | sem erros | sem erros | sem erros |
| Status | ✅ válido | ✅ válido | ✅ válido (após fix) |

**Tendência**: o custo por segundo de vídeo cresce com a duração (mais frames por janela
e, a partir de ~15 s, o overhead de janelas múltiplas + VAE encode do overlap). A margem
de commit cai com a duração (22,8 → 17,3 → 9,3 GB) mas permanece acima do limiar de 5 GB.
Três testes curtos NÃO validam gerações de 5 minutos — ver PROXIMOS_PASSOS.md.

**Status anterior (missão noturna): BLOQUEADO** — documentado abaixo como evidência.
Nenhum vídeo havia sido gerado na missão noturna.

## Configuração comum dos experimentos (base da FASE C)

- Modelo: `minimax_h3_fl2va_pruned` (T2VA: texto → vídeo + áudio integrados)
- Prompt: formato oficial MiniMax H3 com fala pt-BR `<d>[Portuguese] Bom dia! O café de hoje ficou perfeito.</d>`
- Res: 1152×640, 24 fps, 10 s, seed 7001, 6 passos, LoRA turbo Lightx2v FL2V 8-step v1.0 @1.0, guidance 1, flow_shift 12, Spectrum on, SDPA
- Telemetria completa: torch (alocada/reservada/driver) a cada 5 s + sistema (RAM/commit/VRAM dedicada+compartilhada) a cada 5-7 s + eventos com timestamps

## Tabela dos 9 experimentos controlados (uma mudança por experimento)

| # | Data/hora | Mudança única testada | Resultado medido (fase "Encoding Prompt") |
|---|---|---|---|
| 1 | 03:23 | Primeira execução | **Defeito do MEU harness** (loop de log; ver INCIDENTES.md). Interrompida por mim. Download do transformador INT8 (21 GB) preservado |
| 2 | 03:33→03:47 | Baseline: Profile 4 + encoder Quanto INT8 (26,7 GB) + smart_pinning ON | Model Loaded ✓ (VRAM 76 MB — streaming MMGP OK). **CRASH** no encode: margem de commit 262→479 MB, RAM disponível 494 MB, **GPU shared 7,6 GB** (staging ring do MMGP); `c10_hip SetDevice` → abort (0x80000003). Windows expandiu pagefile 18,5→21,6 GB e não bastou |
| 3 | 04:13 | `smart_memory_pinning: false` (sem staging ring) | **CRASH** no mesmo ponto (0xC0000409). Margem 886 MB já no load (pinning de Reserved RAM do Profile 4 ≈ 6 GB) |
| 4 | 04:19 | + `--perc-reserved-mem-max 0.25` | **CRASH** igual (0xC0000409). O budget de pinning do perfil não obedece ao flag nessa fase |
| 5 | 04:29 | **Profile 5** (fail-safe: quase zero Reserved RAM) | **ENCODER FUNCIONOU** (3,25 it/s, 11/50 camadas, VRAM em uso real). Mas margem caiu a 593 MB → **watchdog da missão abortou** (regra: < 5 GB) |
| 6 | 04:35 | config global `text_encoder_quantization=gguf_q4_m` | Seleção errada → baixou encoder **BF16 51,5 GB** (42,9 GB parciais preservados). Abortada por mim |
| 7 | 04:47 | `config:["gguf_q4_k_m"]` (lista) nas settings | Formato errado (deve ser string) → usou INT8; encode funcionou; margem 602 MB → watchdog abortou |
| 8 | 04:54 | **`config:"gguf_q4_k_m"` (string) → encoder GGUF Q4_K_M (14,6 GB) baixado ✓** | Encode funcionou (3 s/it sem kernels HIP GGUF — mais lento). Margem no encode: 1.347 MB → watchdog abortou |
| 9 | 11:11 | **Removido `--preload 6000`** (VRAM no encode só ~1 GB) | Encode a 4,18 it/s (54%, 27/50) funcionando, mas o streaming do encoder consumiu 4,7 GB de commit (staging WDDM) → margem 2.329 MB → watchdog abortou |

## Diagnóstico final (evidências)

1. **O pipeline funciona tecnicamente**: com Profile 5 o modelo carrega, o encoder codifica a
   3–4 it/s, a GPU processa de verdade (VRAM alocada 1–5 GB). Nunca houve falha de modelo,
   prompt, LoRA ou áudio.
2. **O limite é o commit do Windows**: no ROCm/Windows, as transferências de blocos do
   text encoder (26,7 GB INT8 ou 14,6 GB GGUF) usam staging registrado na memória
   compartilhada WDDM, que **conta como commit** (GPU shared 4,7–7,6 GB medidos).
   A carga precisa de ~17+ GB de commit; o limite atual (RAM 15,9 + pagefile 2,9) é 18,5 GB.
   A margem exigida pela missão (≥ 5 GB) é inatingível nessa configuração — por margem
   pequena e consistente (2,3 GB de déficit no melhor caso, experimento 9).
3. **A instalação antiga funcionava por causa do pagefile de ~40 GB** (dado do próprio
   briefing da missão). Após a formatação, o pagefile voltou ao padrão de 2,9 GB.
4. O watchdog que implementei (abortar < 5 GB em 2 amostras) aplicou corretamente a
   regra da seção 12 da missão em todos os casos (exit code 3 documentado).

## Testes 1, 2 e 3 (da FASE D)

**Não executados até o fim** — bloqueio na fase "Encoding Prompt" comum a todos.
O Teste 1 (cena simples) estava configurado pronto para rodar (prompt oficial pt-BR,
settings completos em LOGS/test1_settings.json). Os Testes 2 e 3 dependem do mesmo
desbloqueio. Nenhum vídeo substituto foi fabricado (regra: não inventar resultado).

## Artefatos preservados

- LOGS/TESTE_01_tentativa9_events.jsonl — eventos completos da última tentativa
- LOGS/TESTE_01_tentativa9_mem.csv — telemetria torch da última tentativa
- LOGS/sys_mem_completo.csv — telemetria de sistema de TODAS as tentativas
- LOGS/test1_settings.json — settings prontas do Teste 1 (prontas para reuso)
- LOGS/INCIDENTES.md — incidentes e correções (incl. bug do meu harness, corrigido)
- Modelos baixados (podem ser reutilizados; nada precisa baixar de novo):
  - Transformador INT8 ConvRot pruned (20 GB) ✓
  - **Encoder GGUF Q4_K_M (14,6 GB)** ✓ (nova rota validada p/ baixa RAM)
  - Encoder Quanto INT8 (26,7 GB) ✓ (usável com pagefile maior)
  - VAE vídeo INT8 (2,7 GB) + VAE áudio (577 MB) + latent upscaler (659 MB) ✓
  - LoRA turbo 8-step (1,38 GB) ✓
  - Parcial BF16 encoder (42,9 GB, .incomplete — pode ser concluído ou apagado)
