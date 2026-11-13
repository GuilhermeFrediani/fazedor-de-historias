# P4 — AUDITORIA TÉCNICA DO VEDA SPARSE (SOMENTE LEITURA) — 18/10/2026

**Escopo:** investigação sem download, instalação, alteração ou geração.
**Fontes:** código local WanGP v18.17 (commit fde3c7e), upstream no GitHub/HuggingFace
(metadados e documentos — sem download de modelos), consulta local de propriedades do
ambiente já instalado (torch capability/bf16 — sem geração).

---

## 1. IDENTIFICAÇÃO EXATA DO COMPONENTE (Investigação 1)

| Campo | Valor (evidência) |
|---|---|
| Nome no WanGP | **"Veda Learned Sparse Attention (Triton, NVIDIA SM80+)"** (rotulagem do handler; ver ressalva de rótulo abaixo) — modos `minimax_h3_fl2va_pruned_veda` etc. |
| O que é | Atenção esparsa **aprendida** (distilled predictor decide quais tiles de atenção computar — ~top 10%); paper **"Veda: Scalable Video Diffusion via Distilled Sparse Attention"** (Han et al., ICML 2026, arXiv 2605.30325) |
| Projeto original | **github.com/veda-sparse/Veda-on-ComfyUI** — "Veda Sparse Attention for ComfyUI (MiniMax-H3)", org `veda-sparse`, criado 02/10/2026, 183 stars (NOTICE local aponta a revisão exata `67e4eb55`) |
| Empacotamento no WanGP | Adaptado do upstream: `models/minimax_h3/veda/` (attention.py, plans.py, selection.py, sparse_int8.py, tiling.py, preprocess.py) — predictor gerenciado pelo MMGP, formato próprio `wangp-h3-veda-v1` (50 camadas × 56 cabeças × 128 canais) |
| Kernel | `triton-int8`: QK INT8 / PV FP16, block-sparse 128-tile — **derivado de SageAttention 1.0.6** (Thu-ML, BSD-3-Clause) |
| Licenças | Código upstream: **MIT** (© 2026 veda-sparse) • Kernel INT8: **BSD-3-Clause** (SageAttention 1.0.6, © 2024 Jintao Zhang, Haofeng Huang) • **Pesos do predictor: MiniMax H3 Community License** (herdada do modelo base) |
| Predictor do WanGP | `DeepBeepMeep/MiniMax-H3`: `minimax_h3_t2va_veda_predictor_bf16.safetensors` (**526 MB**) e `..._int8_convrot.safetensors` (**267 MB**) — o modelo Veda **compartilha o MESMO transformador** do pruned normal (URLs idênticas às que JÁ estão no disco) |
| Upstream (ComfyUI) | Predictor "preview" fp8 de 275 MB (`Veda-Sparse/Minimax-H3-T2VA-Veda-8NFE-600Step-Preview`) — **não é o mesmo arquivo** do WanGP (formatos diferentes), mas o MÉTODO e o kernel são os mesmos |

**Identificação inequívoca: SIM.** O componente do plano de otimização ("Veda Sparse") é
exatamente o `minimax_h3_fl2va_pruned_veda` do WanGP, derivado do projeto
`veda-sparse/Veda-on-ComfyUI` com kernel Triton INT8 derivado do SageAttention 1.0.6.
Nomes semelhantes não foram presumidos: tudo foi rastreado pelo NOTICE do próprio código.

## 2. MATRIZ DE COMPATIBILIDADE (Investigação 2)

| Requisito | Status | Evidência (tipo) |
|---|---|---|
| Windows 11 | **CONFIRMADO** | Registro upstream de verificação na **RX 9060 XT + Windows 11** (docs/hardware.md, 10/10/2026): `tests/gpu` 3 passed, erro relativo 1,28–1,33% vs fp32 (doc oficial do projeto) |
| AMD ROCm / gfx1200 (RX 9060 XT) | **CONFIRMADO (kernel)** | Mesmo registro: benchmark do kernel triton-int8 NA NOSSA GPU: 6,5–6,7× entre configs; attention+overhead 4,62× (38k tokens) e 7,77× (104k) vs SDPA AOTriton (doc oficial + medição na GPU exata) |
| Gate de seleção no WanGP | **CONFIRMADO** | `begin_forward` exige capability[0]≥8 e bf16; **medido neste ambiente**: capability **(12,0)**, bf16 OK → gate passa. O rótulo "NVIDIA SM80+" reflete o que foi testado, não uma checagem de código (não há teste `hip is None` nesse caminho) |
| PyTorch **2.13.0+rocm10.0.0** | **PARCIAL** | A verificação na 9060 XT usou torch **2.16.0a0+rocm10.2** + triton-windows **3.8.0**; nosso env tem **2.13.0+rocm10.0.0 + triton 3.7.1.post27**. Mesma família; kernels Triton usam primitivos padrão (tl.load/store, int8) — mas a combinação exata das NOSSAS versões não foi verificada por ninguém |
| WanGP **v18.17** (commit fde3c7e) | **CONFIRMADO** | Integração in-tree neste commit (handler registra os modelos veda; sparse_int8.py presente). Ressalva: integração tem um defeito de configuração para AMD (item 3) |
| Pipeline MiniMax H3 FL2VA INT8 | **PARCIAL** | O model def veda usa o mesmo transformador INT8 ConvRot já instalado + predictor int8_convrot (arquivo existe no HF); `read_metadata` valida o formato no load. Execução completa no nosso pipeline: NÃO VERIFICADA |
| Spectrum com 6 passos | **NÃO VERIFICADO (provável)** | Ortogonais por construção (Veda substitui a atenção DENTRO de cada passo; Spectrum pula passos inteiros). Ninguém publicou a combinação Veda+Spectrum |
| Geração de **áudio** (T2VA/FL2VA) | **PARCIAL/NAO VERIFICADO** | O predictor é "T2VA" (tarefa vídeo+áudio conjunta do H3) e o e2e upstream rodou T2VA FL2VA int8 completo — MAS nenhuma comparação de QUALIDADE de áudio com atenção densa foi publicada (upstream: "vídeos gerados aguardam comparação manual"). Risco específico: inteligibilidade da fala pt-BR sob 90% de esparsidade |
| `kernel_precision: "strict"` (obrigatório nosso) | **COMPATÍVEL COM CUSTO** | O kernel esparso RODA em strict (só o auto-tuner é desligado); PORÉM o fallback fixo `_launches[0]=(4 warps)` é a config que o upstream mediu **6,5× mais lenta em HIP** — ver item 3.2 |
| Watchdog v2 | **SEM CONFLITO** | Veda não altera monitoring; atenção extra: Veda adiciona ~0,7–1,3 GB de VRAM (tabela 5070: pico 1,31 GB vs 0,64 denso) — os limiares do watchdog cobrem |

**Classificação por tipo de evidência:** doc oficial upstream + medição na GPU exata
(gfx1200/Windows) = a melhor evidência possível sem rodar aqui; relatos de usuário =
nenhum relevante para RDNA4; inferência própria = marcada como tal (modelo quadrático
do passo, ver FONTES).

## 3. INTEGRAÇÃO E RISCOS (Investigação 3)

### 3.1 O que muda para ativar (sem aplicar nada agora)
1. **Settings da geração**: `model_type: "minimax_h3_fl2va_pruned_veda"` (chave única;
   tudo o mais — passos, seed, Spectrum, resolução, LoRA — idêntico; o handler força
   `override_attention="veda"` sozinho)
2. **Download na 1ª utilização**: somente o predictor — **267 MB** (int8_convrot, o que
   casa com nossa quantização) ou no máximo **~793 MB** (se as duas variantes baixarem).
   O transformador (20 GB) **NÃO baixa de novo** (URLs idênticas ao pruned normal)
3. Nenhum outro arquivo/dependência muda: kernel Triton já no código; Triton já instalado

### 3.2 ACHADO CRÍTICO — configuração de launch no modo strict
`sparse_int8.py:127-133`: com `kernel_precision="fast"`, um `_tuner` faz benchmark e
escolhe a config; com **"strict"** (nosso obrigatório), usa fixo `_launches[0]` =
**(4 warps, 3 stages)**. O registro upstream na NOSSA GPU: **(4,3) = 391,7 ms vs
(8,3) = 60,5 ms** por kernel (latent_t 37) — **6,5× mais lento**. Ou seja: em strict,
a integração WanGP roda o Veda com a config errada para HIP. Mesmo assim, atenção-level
em strict ≈ 1,8–2,4× mais rápida que SDPA (contas na FONTES), porque a esparsidade (90%
pulado) compensa em parte a config ruim. **Duas saídas possíveis** (ambas exigem sua
autorização futura): (a) aceitar o ganho reduzido do strict; (b) patch de 1 linha
(`_launches[0]` → `(8, 3)`), reversível e respaldado pela medição upstream NA NOSSA GPU
(diff proposto no PLANO_ROLLBACK); (c) usar `fast` somente em teste de janela única
(a falha CUTLASS só existe no VAE encode de janelas múltiplas) — conflita com a regra
"preservar strict", portanto só com autorização explícita.

### 3.3 Riscos técnicos identificados
| Risco | Severidade | Mitigação |
|---|---|---|
| Config 4-warp no strict (6,5× kernel) | Média | opções 3.2(b)/(c); mesmo sem elas há ganho líquido |
| Predictor treinado em 1344×768/1024×768/768²/768×1344 @ 5/10/14 s + 8-step Turbo — nosso 1152×640/6 passos está FORA da distribuição de treino | Média | upstream: funciona com "nearest plan", mas manda COMPARAR vs atenção cheia — teste A/B obrigatório |
| Qualidade do ÁUDIO sob esparsidade: nada publicado | Média/Alta para o projeto | A/B de fala pt-BR obrigatório (loudness + sua escuta) |
| +0,7–1,3 GB VRAM (tiles+predictor+índices) | Baixa em T1/T2 (pico 8,8–9,2/16 GB); Atenção em janelas (T3 chegou a 16,05 GB no VAE encode) | watchdog v2 ativo; testar janela única primeiro |
| Versões torch 2.13/triton 3.7.1 vs verificadas 2.16a/3.8 | Baixa | kernels usam primitivos padrão; primeira execução valida (compila Triton on-demand) |
| `cuda_graphs: []` (veda declara não suportar CUDA graphs) | Nula | não usamos CUDA graphs no fluxo atual |
| Desvio numérico INT8 (1,28–1,33% vs fp32, medido na nossa GPU) | Inerente ao método (igual ao sm120) | A/B visual; é a mesma aritmética do SageAttention 1.0.6 |

### 3.4 Procedimento de rollback (detalhado no P4_VEDA_PLANO_ROLLBACK.md)
Resumo: voltar `model_type` para `minimax_h3_fl2va_pruned` (1 chave). Nada é desinstalado;
o predictor (267–793 MB) fica no disco e pode ser apagado manualmente. O ambiente
funcional atual (T1/T2/T3 validados) permanece intacto durante o teste — o modelo veda
é uma ENTRADA diferente, não uma substituição.

## 4. TABELA FINAL (síntese para decisão)

| Dimensão | Avaliação |
|---|---|
| Compatibilidade HW/SW | **CONFIRMADA no kernel** (upstream mediu na GPU exata: RX 9060 XT/Win11/ROCm), **PARCIAL** no nosso par torch 2.13/triton 3.7.1 e na integração WanGP (defeito de config 4-warp no strict) |
| Qualidade/confiabilidade das evidências | **Alta** (doc oficial do projeto + log de medição por hardware + paper ICML 2026 + código local auditado); zero evidência anecdótica usada |
| Ganho esperado (atenção) | Medido na nossa GPU (upstream): 4,62× (38k tok) / 7,77× (104k tok) com config certa; **1,8–2,4× com a config do strict** |
| Ganho esperado (fim-a-fim, extrapolado) | No nosso passo (modelo quadrático ajustado aos nossos 3 testes, atenção ≈ 63–64% do passo): **~1,4–1,6× em strict; ~1,7–1,9× com config certa** → difusão de 5 min: 27,6k s → **~17–20k s (strict) / ~15–16k s (tunada)**; total 5 min: **~5,8–6,4 h (strict) / ~5,2–5,6 h (tunada)** vs 9,1 h atual |
| Risco técnico | Médio (fora da distribuição de treino em 1152×640; áudio não validado; config strict subótima; +VRAM coberto pelo watchdog) |
| Custo de instalação | **Baixo**: download 267 MB (máx. 793 MB), zero reinstalação, zero compilação (Triton JIT já funcional), reversível com 1 chave |
| **Recomendação** | **AVANÇAR PARA TESTE** — com pré-condições: (1) A/B janela única (T1-equivalente, seed 7001, mesmo prompt) comparando tempo/VRAM/qualidade+áudio; (2) decidir antes a questão strict×launch config (aceitar ganho menor, autorizar patch de 1 linha, ou autorizar fast só no teste de janela única); (3) só testar janelas múltiplas após aprovação do A/B; (4) áudio pt-BR obrigatório na comparação |

**Bloqueios declarados:** nenhum na investigação. O que permanece NÃO VERIFICADO até um
teste autorizado: execução real no nosso par torch/triton, qualidade em 1152×640 (fora do
treino), qualidade de áudio sob esparsidade, e o ganho fim-a-fim (toda projeção acima é
extrapolação ancorada em medições da mesma GPU — não é resultado no nosso pipeline).
