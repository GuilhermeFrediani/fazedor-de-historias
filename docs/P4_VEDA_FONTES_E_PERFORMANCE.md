# P4 — FONTES E PERFORMANCE DO VEDA SPARSE (somente leitura) — 18/10/2026

## 1. Origem exata dos números que circularam

| Alegação | Origem exata | O que diz a fonte |
|---|---|---|
| "Veda Sparse… **up to 2x faster** for higher-resolution or longer videos" | WanGP **CHANGELOG v18.00** (11/10/2026) e descrição do model def local | Resumo do integrador (DeepBeepMeep). Sem hardware/condições declarados. Não é medição no seu hardware |
| "20%–45%" (meu PLANO_OTIMIZACAO anterior) | **Minha extrapolação conservativa** do "up to 2x" — nunca medida aqui | Estava mal calibrada: a evidência nova (ver §2) sustenta faixas maiores na atenção, mas o fim-a-fim depende da fração de atenção no SEU passo |
| "2.9× end to end, 7.1× attention" | README upstream **e2e medido** | RTX 5070 12 GB, Windows 11, ComfyUI, T2VA FL2VA int8 + **8-step Turbo LoRA**, **1344×768, 124 frames (5,2 s)**, 8 passos, seed 42: 40,7 s/passo → 14,0 s/passo (atenção 31,1→4,41 s/passo) |
| "4,62× / 7,77× na atenção" | **docs/hardware.md upstream, registro de 10/10/2026 — NA SUA GPU** | **Radeon RX 9060 XT 16 GB, Windows 11**, bench de 1 camada com scorer aleatório, 90% esparsidade, incl. scoring+gather+scatter: SDPA (AOTriton flash) 1016,6 ms → Veda 220,2 ms em 38.228 tokens (latent_t 37); 7991,0 → 1028,3 ms em 104.484 tokens (latent_t 102) |
| "6,5×/6,7× entre launch configs" | Mesmo registro (tune_int8 na 9060 XT) | 4 warps/3 stages = 391,7 ms vs **8 warps/3 stages = 60,5 ms** (latent_t 37); 2530,5 vs 378,6 ms (latent_t 102). Conclusão upstream: "HIP上 8 warps" obrigatório |
| Erro numérico 1,28–1,33% | Mesmo registro (tests/gpu na 9060 XT) | vs fp32: denso/10% esparso/padding; idêntico ao sm120 (1,34%) — a aritmética é a do SageAttention 1.0.6 |

**Nenhum número acima foi medido no SEU pipeline** (WanGP/Profile 5/Spectrum/GGUF).
O que é medida NA SUA GPU: o kernel de atenção isolado (upstream, ComfyUI-side).
O que é medida NO SEU PIPELINE: os passos ~170/232/332 s dos T1/T2/T3 (nossos testes).

## 2. Conversão para o SEU caso (tudo marcado: medido × extrapolado)

**2.1 Tokens dos seus vídeos (inferência, marcada como extrapolação):** o upstream
reporta ~1024 tokens/latent_t em 16:9 (1344×768). Proporcional à área: 1152×640
(0,71×) → ~731 tokens/latent_t. T1 (243 f, latent_t≈62) ≈ **45k tokens**; T3-janela
(362 f, latent_t≈92) ≈ **67k tokens**. Seus casos ficam ENTRE os dois pontos medidos
na sua GPU (38k e 104k) — zona interpolada, não extrapolada para fora.

**2.2 Fração de atenção no seu passo (modelo próprio, ajustado aos SEUS dados):**
Ajustei passo(T) = a·T² + b·T sobre T1/T2/T3 (T em k-tokens): **a=0,0534 s/k²,
b=1,375 s/k** — reproduz os três testes com erro ≤1% (T1 170 ✓, T2 230 vs 232 ✓,
T3 332 ✓). Termo quadrático (atenção) ≈ **63–64% do passo** nos seus tamanhos.
(Estrutura consistente com o e2e do 5070, onde atenção era 31,1/40,7 = 76% em 104k tokens.)

**2.3 Projeção de ganho (EXTRAPOLAÇÃO ancorada em medições da mesma GPU):**

| Config do kernel | Atenção-level na sua GPU (interp. 45–67k) | Passo esperado (T1: 170 s) | Passo esperado (T3-janela: 332 s) | Ganho fim-a-fim difusão |
|---|---|---|---|---|
| **strict (4 warps)** — como o WanGP roda hoje | ~1,8–2,4× | ~107–122 s (1,4–1,6×) | ~211–240 s (1,4–1,6×) | **~1,4–1,6×** |
| **8 warps (tunada/patch)** — como o upstream mediu | ~4,6–6,5× | ~97 s (1,75×) | ~174 s (1,9×) | **~1,7–1,9×** |

Contas (exemplo T1 strict): atenção 108 s ÷ 2,4–1,8 ≈ 45–60 s + resto 62 s ≈ 107–122 s.
Todos os números desta tabela são **projeções** — nenhum foi medido no seu pipeline.

**2.4 Efeito no vídeo de 5 minutos (projeção a partir do modelo auditado):**
Difusão conservadora 27.615 s (21 janelas) → **strict: ~17,4–19,9k s; tunada: ~14,7–16,0k s**.
Total (difusão+áudio 3.510 s+overheads ~1.480 s):
- Hoje (medido/extrapolado): **~9,1 h**
- Veda strict (projetado): **~6,0–6,7 h** — entra na sua janela de 6–8 h
- Veda tunado (projetado): **~5,4–5,8 h** — folga extra
- O ganho cresce com janelas maiores (atenção ∝ T²) — as janelas de 362 frames do 5 min
  estão na zona boa (67k tokens)

## 3. Qualidade (o que existe e o que falta)

| Aspecto | Evidência existente |
|---|---|
| Precisão numérica | Medida na SUA GPU: 1,28–1,33% vs fp32 (mesma do sm120 e do SageAttention 1.0.6 — upstream: "the quality is what that path gives") |
| Vídeo | Upstream e2e em 1344×768/8-step rodou, mas "vídeos gerados aguardam comparação manual" — nenhuma comparação publicada. RTX PRO 6000: flicker/tile-artifact NÃO reproduziram (métricas com 8–10 seeds) — sinais de robustez, mas em r2va/ref2va |
| Treino do predictor | **1344×768, 768×1344, 768×768, 1024×768 @ 5/10/14 s com 8-step Turbo. SEU 1152×640 e 6 passos = fora da distribuição** ("other sizes fall back to nearest plan… compare them against full attention") |
| Áudio | **NADA publicado** sobre qualidade de áudio sob esparsidade (o predictor é T2VA = vídeo+áudio conjuntos; e2e rodou com áudio, sem avaliação publicada) → risco específico para a sua fala pt-BR |
| Espectro/6 passos | Combinação inédita (ortogonal por construção; não verificada) |

## 4. Resumo de honestidade

- **Medido na sua GPU** (pelo upstream, não por nós): kernel funciona, erro 1,3%,
  atenção 4,6–7,8× (config certa) / 2,6–3,2× (config 4-warp), launch 8-warp obrigatório.
- **Medido no seu pipeline** (por nós): passos de 170/232/332 s; atenção ≈63–64% do passo
  (modelo ajustado, R² com erro ≤1%).
- **Projetado (extrapolação)**: 1,4–1,9× na difusão; 5 min em ~5,4–6,7 h.
- **Não verificado em lugar nenhum**: execução no SEU par torch 2.13/triton 3.7.1 +
  WanGP + Spectrum + 6 passos; qualidade visual em 1152×640; qualidade de áudio pt-BR.
- Nenhuma alegação de fabricante foi apresentada como resultado comprovado no seu
  hardware — o texto acima separa sempre as três camadas.
