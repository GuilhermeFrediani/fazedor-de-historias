# Benchmark de velocidade — 25/11/2026

**Objetivo:** cortar o tempo de produção sem perder a qualidade aprovada na fumaça de 60 s
(8 steps, 1152×640, 16,2 min/clipe → 2h10 por minuto de vídeo).

**Método:** mesmo clipe (c01 "Brilho de Última Hora"), mesma âncora, mesmo prompt, seed 8100,
mesmo driver (`gen_test.py`), perfil 5, `--max-ram 24`. Frames extraídos em 5,0 s e 9,9 s.

## Resultados medidos

| Config | LoRA | Tempo/clipe (10 s) | 1 min de vídeo | 10 min de vídeo | Qualidade |
|---|---|---|---|---|---|
| 8 steps, 640p (aprovado) | sim | 16,2 min | 1h37 | ~16h | ✅ referência |
| 8 steps, 480p | sim | **7,2 min** | 43 min | ~7,2h | ✅ muito boa |
| 4 steps, 640p | sim | **10,3 min** | 1h02 | ~10,3h | ✅ ~idêntica ao aprovado |
| 4 steps, 480p | sim | **4,9 min** | **29 min** | **~4,9h** | ✅ boa |
| **2 steps, 640p** | sim | **7,6 min** | 46 min | ~7,6h | ✅ boa |
| **2 steps, 480p** | sim | **3,9 min** | **23 min** | **~3,9h** | ✅ boa (mesmos beats do aprovado) |
| 4 steps, 640p | **não** | 10,1 min | — | — | ❌ fantasmas |
| 2 steps, 640p | **não** | 7,5 min | — | — | ❌ fantasmas |
| 4 steps, 480p | **não** | 4,9 min | — | — | ❌ fantasmas |

**Conclusão 1:** o turbo LoRA `lightx2v_8step_alpha8` é **obrigatório**. Sem ele o H3 colapsa
em 4/2 steps (bonecos viram ruído multicolorido). Com ele, 4 steps funciona.
**Conclusão 2:** a resolução é a alavanca mais forte: 640p → 480p corta ~55% do tempo
(16,2 → 7,2 no 8 steps; 10,3 → 4,9 no 4 steps; 7,6 → 3,9 no 2 steps).
**Conclusão 3:** com o LoRA, **2 steps também sobrevive** em 480p. O contact sheet (1 frame/s)
do 2 steps mostra a mesma sequência de planos do clipe aprovado de 8 steps (relógio macro →
wide → TÉO cobre o rosto → envelope), sem fantasmas nem cortes espúrios.

## Gate de visão no 2 steps / 480p

Rodado com as mesmas regras do episódio (`qc_visao.gate_ancora`, 5 frames: 9.9/5.0/3.0/2.0/0.8):

- **4/5 frames APROVADOS** (5.0 s e os 3 insertos).
- **1 apontamento em 9.9 s**: "régua dobrável 0 visível / relógio de bolso 0 visível".
- Esse apontamento é o **mesmo falso-positivo de calibração já registrado no clipe aprovado de
  8 steps** (rejulgamento c01): os props estão ocultos no fim, não ausentes. **Não é defeito
  do 2 steps.**

Conclusão: sob o mesmo juiz, o 2/480 se comporta como o aprovado — sem modo de falha novo.
O ajuste fino do gate (prop oculto ≠ ausente) segue como item de calibração do pipeline.

## Kandinsky 6 Lite 3B (bf16)

- int8 **não roda** na RX 9060 XT (RDNA4/gfx1200) com ROCm 10.2: kernels
  `quanto_int8_triton`/`convrot_int8_triton` sem matrix core i8. bf16 é obrigatório.
- bf16: load 0,1 min, encoder 0,2 min, **inferência 3,6 min (5 s, 480p, 10 steps)**,
  **VAE decode ~7 min** (128 tiles) e **cancelamento por commit de RAM** (16 GB físicos).
- Projeção: ~11 min por 5 s ≈ **2,2 min por segundo de vídeo** — pior que o H3 4/480
  (0,49 min/s). **Linha encerrada** para produção neste hardware.

## Recomendação

| Modo | Config | Uso |
|---|---|---|
| **Produção rápida (padrão)** | H3 **2 steps**, 832×480, LoRA | 1 min em ~23 min; **10 min em ~3,9h** |
| **Fallback seguro** | H3 4 steps, 832×480, LoRA | 1 min em ~29 min; 10 min em ~4,9h |
| **Qualidade máxima** | H3 4 steps, 1152×640, LoRA | 1 min em ~1h; 10 min em ~10h |
| **Meio-termo** | H3 8 steps, 832×480, LoRA | 1 min em ~43 min |

**Estratégia de produção:** renderizar em 2/480 por padrão; o gate de visão julga como sempre.
Se um clipe for reprovado no gate, re-renderizar **aquele clipe** em 4/640 (10,3 min) — o custo
do retrabalho é baixo e a qualidade final fica garantida pelo mesmo juiz.

- **Upscale 480p → 720p/1080p** (spatial upsampler) é o próximo teste para YouTube.
- **Gate em paralelo com o render** (hoje o gate bloqueia a GPU ~2–3 min por clipe):
  corta ~2h num vídeo de 10 min. Próximo passo de engenharia.
- Os settings de teste estão em `C:\Users\Guilherme\Documents\Projeto Padrão\bench_h3_*_settings.json`;
  os vídeos em `C:\pinokio\api\wan2gp-amd\app\outputs\bench_h3_*_lora.mp4`.
