# AUDITORIA DE PERFORMANCE E QUALIDADE — MINIMAX H3 (18/10/2026)

**Escopo:** Testes 1, 2 e 3 (v18.17 recuperado). Somente leitura — nenhuma geração/alteração.
**Fontes:** eventos JSONL (535 eventos), telemetria torch (1.068 amostras), settings
efetivos, hashes, PATCHES_DIFF.md, relatórios por teste, telemetria de sistema da missão
noturna (para contexto do bloqueio), briefings históricos do v17.10 (do usuário).

---

## 1. TABELA DE TEMPOS POR ETAPA (medidos nos eventos; relógio do sistema)

### Teste 1 — 10,125 s / 243 frames / 1 janela — total 846 s
| Etapa | Início | Duração |
|---|---|---|
| Carga do modelo | 12:47:51 | 3 s |
| Encode do prompt (50 camadas, 6,70 it/s) | 12:47:54 | 10 s |
| **Difusão (4 âncoras + 2 replays)** | 12:48:04 | **683 s** |
| VAE decode (flush final; pipelined) | 12:59:27 | 1 s |
| **Áudio estéreo H3** | 12:59:31 | **137 s** |
| Save MP4 | 13:01:48 | 1 s |

### Teste 2 — 12,25 s / 294 frames / 1 janela — total 1.110 s
| Etapa | Início | Duração |
|---|---|---|
| Carga | 13:27:08 | 3 s |
| Encode do prompt (6,79 it/s) | 13:27:11 | 10 s |
| **Difusão (4 âncoras + 2 replays)** | 13:27:21 | **932 s** |
| VAE decode (flush) | 13:42:53 | 1 s |
| **Áudio** | 13:42:57 | **151 s** |
| Save | 13:45:28 | 2 s |

### Teste 3 (retry válido) — 18,79 s / 451 frames / 2 janelas — total 1.866 s
| Etapa | Janela | Início | Duração |
|---|---|---|---|
| Carga | — | 15:00:22 | 3 s |
| Encode prompt (6,1 it/s) | J1 | 15:00:25 | 11 s |
| **Difusão J1 (362 frames; 4×~332 s)** | J1 | 15:00:36 | **1.331 s** |
| VAE decode flush (pipelined) | J1 | 15:22:47 | 1 s |
| **Áudio J1 (15,08 s de áudio)** | J1 | 15:22:52 | **176 s** |
| Save checkpoint J1 | J1 | 15:25:48 | 3 s |
| **VAE encode do overlap (18 tiles)** | J2 | 15:25:51 | **40 s** |
| Preparing conditioning | J2 | 15:26:31 | 9 s |
| Encode prompt J2 | J2 | 15:26:40 | 20 s |
| **Difusão J2 (107 frames; 4×~53 s)** | J2 | 15:27:00 | **214 s** |
| VAE decode flush | J2 | 15:30:34 | 0 s |
| **Áudio J2 (3,7 s)** | J2 | 15:30:35 | **44 s** |
| Save final | J2 | 15:31:19 | 3 s |

(Tentativa 1 do T3, kernel `fast`: J1 idêntica em 1.332 s; falhou no VAE encode do overlap
em 0 tiles — ver TESTE_03\RELATORIO_TESTE_03_TENTATIVA1_FALHA.md.)

## 2. PASSOS DE DIFUSÃO INDIVIDUAIS — Spectrum (medido)

| Teste/janela | Frames | Passo 0 | Passo 1 | Passo 2 | Passo 3 | Passo 4 | Passo 5 |
|---|---|---|---|---|---|---|---|
| T1 | 243 | **174 s** | ~0 s | **169 s** | ~1 s | **168 s** | ~169 s |
| T2 | 294 | **233 s** | ~0 s | **232 s** | ~1 s | **232 s** | ~232 s |
| T3-J1 | 362 | **334 s** | ~1 s | **331 s** | ~1 s | **332 s** | ~331 s |
| T3-J2 | 107 | ~53 s | ~0 s | ~53 s | ~0 s | ~54 s | ~54 s |

**FATO COMPROVADO (item 4):** o padrão Spectrum é **R, S, R, S, R, R** em todas as
janelas — **4 passos de âncora (transformer completo) + 2 passos de "smoothing replay"
(transformer-free, ~0–1 s)**. Exatamente os "~2 de 6 ignorados" do ambiente v17.10
citados no seu briefing. Trabalho efetivo de transformer: 66,7% do nominal de 6 passos
(o Spectrum já entrega 33% de economia; os 6 passos semânticos são preservados).

## 3. PARIDADE DE CONFIGURAÇÃO/CÓDIGO ENTRE OS TESTES (item 3)

**Verificado por hash:** `gen_test.py` e `test1_settings.json` usados no Teste 1 (cópia
via wrapper pós-reboot) são **byte-idênticos** (SHA-256) aos do workspace usados nos
Testes 2/3. **Settings efetivos idênticos** nos 3 testes (lidos dos settings_efetivas):
passos=6, 1152×640, 24 fps, seed 7001, spectrum 25%/0,08, euler, LoRA 1.0,
janela 362/overlap 18, sem imagens de referência (`video_prompt_type` vazio,
`audio_prompt_type` vazio — **T2VA puro, texto→vídeo+áudio**).

**Diferenças reais encontradas (todas):**
1. **`kernel_precision`: "fast" nos Testes 1, 2 e T3-tentativa1 → "strict" no T3-retry**
   (correção do bug CUTLASS). Efeito medido na difusão da J1: **1.331 s (strict) vs
   1.332 s (fast) — custo zero** no caminho principal; afeta apenas os kernels fundidos
   de VAE (o caminho `strict` é o que funciona em AMD).
2. Conteúdo: prompts, durações (10/12/18 s), `output_filename` — por design dos testes.
3. Local de execução do T1 (pasta temp, mesmo binário) — sem efeito funcional.

## 4. ESTRUTURA DE JANELAS E REPROCESSAMENTO (item 5) — hipótese REFUTADA

**FATO:** a Janela 2 do T3 processou **107 frames** (89 novos + 18 de overlap), **não**
uma janela cheia de 362. Difusão J2 = 214 s ≈ 4×C(107) ✓. O overlap reprocessado
(18 frames) é **17% do trabalho da J2** — não há reprocessamento acumulado de conteúdo
de janelas anteriores, nem growth de custo por janela por acúmulo. O decode VAE é
**pipelined com a difusão** (flush final de 0–1 s; tiles decodificados progressivamente),
e o áudio é decodificado **por janela, apenas do seu segmento** (176 s p/ 15,08 s de
áudio da J1; 44 s p/ 3,7 s da J2 — taxa constante ~11,7 s por s de áudio).

## 5. MODELO DE CUSTO MEDIDO E VALIDADO

Ajuste por mínimos quadrados sobre os passos-âncora medidos (1152×640, INT8 pruned 20B,
RDNA4):

**C(W) = 0,2508·W + 0,001839·W² segundos por passo-âncora** (W = frames da janela)

| Verificação | Medido | Modelo | Erro |
|---|---|---|---|
| T1 (W=243) | 170 s | 169,5 s | −0,3% |
| T2 (W=294) | 232 s | 232,7 s | +0,3% |
| T3-J1 (W=362) | 332 s | 331,8 s | −0,1% |
| T3-J2 (W=107) | ~53,5 s | 47,9 s | −10,5% (overhead de condicionamento por passo) |
| **Total T1** | 846 s | 854 s | +1,0% |
| **Total T2** | 1.110 s | 1.121 s | +1,0% |
| **Total T3** | 1.866 s | 1.853 s | −0,7% |

Custo marginal fortemente superlinear (atenção ~O(W²)): janelas de 362 frames custam
~2× uma de 243 — **janelas menores são proporcionalmente muito mais baratas por frame**.

## 6. v17.10 (antigo) vs v18.17 (recuperado) (item 6 — só com dados existentes)

| Aspecto | v17.10 (seus registros) | v18.17 (medições atuais) | Comparável? |
|---|---|---|---|
| PyTorch/Triton/Python | 2.13.0+rocm10.0.0 / 3.7.1.post27 / 3.12.10 | idem / idem / 3.12.13 | mesma stack (proposital) |
| Spectrum ~2 de 6 pulados | relatado por você | **confirmado igual (R,S,R,S,R,R)** | ✓ |
| SDPA vs Sage | Sage ~49%/passo mais lento (sua medição antiga) | SDPA usado; Sage não instalado | razão antiga mantida como regra |
| T-FUSE | presente | **não existe mais** | sem equivalente |
| Preload 6000 | usado | removido (pressão de commit na época) | reavaliável agora (47 GB de limite) |
| MMGP | 4.0.0 standalone | integrado ao repo | estrutural |
| Tempos absolutos antigos | **NENHUM registro disponível** | medidos | **IMPOSSÍVEL comparar velocidade** — dado ausente |
| VRAM em janelas múltiplas | "pressão severa" (qualitativo) | pico 16,05 GB em 1 amostra (T3) | só qualitativo |

**Nenhuma comparação de desempenho absoluto antigo×novo é apresentada por falta de
dados equivalentes — explicitamente.**

## 7. FASE 4 — QUALIDADE DO TESTE 3 (defeitos relatados por você)

**Seus relatos:** (a) muda/planta aparecendo no bico do regador; (b) ação inicial
"regando a pia"; (c) consistência do regador/planta entre janelas.

**Classificação por evidência:**
- **Falha técnica: DESCARTADA.** Decode completo sem erros, nenhum NaN/HIP, integridade
  OK, emenda em ~15,08 s com silêncio natural de áudio (14,30–15,05 s). Não há corrupção.
- **Frames de referência: INEXISTENTES** (settings comprovam T2VA puro). O defeito não
  pode vir de imagens de referência.
- **Localização temporal:** os defeitos (a)/(b) ocorrem na ação inicial de regar
  (~2–8 s — janela 1, muito antes da emenda). Portanto **erro semântico do
  modelo/prompt**, não artefato de emenda de janelas. O item (c) requer sua checagem nos
  frames extraídos ao redor da emenda (14,7→15,5 s) e dentro da J1.
- **Hipótese de causa (prompt):** a sequência concentra 3 elementos de água próximos —
  pia (origem), regador (instrumento), planta (destino) — mais 10 ações encadeadas em
  18 s num único plano contínuo. Fusão de papéis (pia→destino da água) e ligação
  regador↔planta (muda no bico) são os erros esperados desse padrão. **Hipótese, não
  fato** — validável regenerando com prompt reestruturado (ver PLANO_OTIMIZACAO).

**Frames extraídos para sua inspeção (leitura, sem gerar nada):**
- `TESTE_03\ANALISE\frames_acao_rega\` — 24 frames: 1,0→9,0 s (passo 0,5 s) + 14,7→15,5 s
  (emenda, passo ~0,1 s) — Use-os para localizar (a), (b) e checar (c).

## 8. FATOS × HIPÓTESES × DADOS AUSENTES

**FATOS (medidos/verificados):** todas as durações das tabelas; padrão Spectrum
4+2; janela 2 = 107 frames (sem reprocessamento); decode pipelined; áudio a 11,7 s/s;
paridade de settings; custo zero do `strict` na difusão; C(W) com erro ≤1% nos totais;
pico VRAM 16,05 GB/driver 0 MB em 1 amostra (T3, VAE encode J2); defeitos do T3 não são
técnicos e estão na J1; sem frames de referência.

**HIPÓTESES (a validar):** causa dos defeitos semânticos = estrutura do prompt (fusão
pia/regador/planta); preload 6000 pode reduzir s/passo agora que há commit disponível;
Veda Sparse entrega 20–2× na difusão (claim do fabricante, não medido aqui); INT8
encoder é mais rápido que GGUF pós-reboot (dados noturnos eram inválidos por thrashing).

**DADOS AUSENTES:** tempos absolutos do v17.10 (impossibilita comparação de desempenho
entre versões); medição de RIFE ×2 e upscale (nada executado); ganho real do Veda/WGPKernels
nesta GPU; qualidade subjetiva dos vídeos (depende de você — frames prontos).
