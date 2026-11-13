# PIPELINE TÉO & JUCA v2.1 — Configuração + Estrutura de Prompts
*Consolidado em 26/10/2026 · Base: guia oficial do H3 (prompt_enhancer.py no WanGP) + 20+ gerações medidas + 3 episódios completos (ZJ, A Cadeira, O Quadro)*

---

# PARTE 1 — PIPELINE ATUAL (exatamente como está configurado)

## Hardware / Sistema
| Item | Valor |
|---|---|
| GPU | AMD RX 9060 XT 16GB (gfx1200) — ROCm |
| CPU/RAM | Ryzen 7 7700 · 16GB RAM · pagefile 32GB |
| Stack | PyTorch 2.13.0+rocm10.0.0 · Triton 3.7.1.post27 · WanGP v18.18 (API) · Pinokio |
| Regra AMD | `kernel_precision: strict` (fast mode = crash CUTLASS) |

## Modelo e configuração
| Item | Valor |
|---|---|
| Modelo | MiniMax H3 FL2VA Pruned 20B (`minimax_h3_fl2va_pruned`) |
| Quantização | GGUF Q4_K_M |
| **LoRA** | **turbo 8-step (lightx2v), multiplicador 1.0 — OBRIGATÓRIO** (sem ele: −60% nitidez, provado por metadata 0/38) |
| Passos | 6 (vídeo) + 3 (áudio, default) |
| Resolução/FPS | 1152×640 @ 24fps forçado |
| Seed | 7001 (comparabilidade) |
| Cache | spectrum (0.08 / 25%) |
| CLI | `--attention sdpa --profile 5` |
| Áudio | NATIVO AAC 32kHz estéreo (pelo prompt multimodal) |

## Settings JSON (template de cada plano)
```json
{
  "model_type": "minimax_h3_fl2va_pruned",
  "num_inference_steps": 6,
  "resolution": "1152x640",
  "force_fps": 24,
  "video_length": "8s",
  "seed": 7001,
  "guidance_scale": 1,
  "flow_shift": 12,
  "skip_steps_cache_type": "spectrum",
  "audio_prompt_type": "",
  "activated_loras": ["https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/loras/minimax_h3_lightx2v_fl2v_turbo_8step_alpha8_v1.0_bf16.safetensors"],
  "loras_multipliers": "1.0",
  "output_filename": "<episodio>_s<n>_<titulo>",
  "config": "gguf_q4_k_m",
  "_cli_extra": ["--profile", "5"],
  "prompt": "<ver PARTE 2>"
}
```

## Regras duras (limites MEDIDOS)
1. **Janela única: máx 362 frames = 15,08s.** Na prática: **planos de 7–10s** (o custo/segundo cresce: 71→99 s/s conforme a duração sobe).
2. **>15s = multi-janela = risco real de crash CUTLASS** (TESTE_03: 1.542s perdidos; retry custou 26 min).
3. **Sem o LoRA = 6 steps sub-denoisado** → o gate `validar_lora` rejeita (checa a metadata embutida do MP4).
4. Watchdog v2 ativo durante toda geração (VRAM >15/15,5GB · commit <5GB · driver <300/50MB · HIP fatal → abort).
5. Limite oficial de prompt: ~7.000 caracteres (API). Os nossos: ~2.500–3.500 — dentro.

## Fluxo de produção (3 etapas, sem re-encode)
```
1. gen_test.py --settings <plano>.json --tag <TAG>   (telemetria + watchdog)
2. GATE: validar_lora() — LoRA na metadata + specs     (clipé sem LoRA = rejeitado)
3. Concat lossless (-c copy) → episódio final          (montagem em segundos)
```

## Performance medida (tabela de custo)
| Duração pedida | Frames | Tempo medido | s/s |
|---|---|---|---|
| 7s | 175 | 8,7–10,9 min | 71–82 |
| 8s | 192 | 10,2–11,1 min | 76–84 |
| 9s | 226 | 12,9–13,4 min | 85–86 |
| 10s | 243 | 14,1–15,0 min | 83–89 |
| 12s | 288 | 18,5 min | 91 |
| 18s (2 janelas!) | 451 | 31,1 min | 99 |

**Episódios de ~50s (6 planos): 66–69 min de geração (80–81 s/s).**
**Escala: 1 min de vídeo ≈ 1,4h · episódio de 5 min ≈ ~7h (lote noturno).**

---

# PARTE 2 — ESTRUTURA DE PROMPTS PARA HISTÓRIAS

## O esqueleto oficial (3 campos, parseados pelo WanGP)
```
integrated_multimodal_description: [Shot 1] <BLOCO VISUAL>
overall_soundscape: <EVENTOS SONOROS NOMEADOS>
non_diegetic_music: N/A
```

## A ordem interna do BLOCO VISUAL (fórmula validada em 18 planos)
```
[Shot 1]
1. ESTILO com artefatos do meio
   "Claymation plasticine stop-motion style, handcrafted modelling clay puppets
   with visible fingerprints, tool marks and thumb-pressed texture, matte with a
   gentle satin sheen, filmed on a miniature practical set."
   → nomear os ARTEFATOS (impressões digitais, marcas de ferramenta) é o que
     vende o estilo, não só o nome do estilo (confirmado pelo guia oficial+web).
2. SET FIXO + LUZ (verbatim em TODOS os planos — âncora de consistência)
3. OBJETOS DE ESTADO (o que muda por plano: cadeira, quadro, bandagem —
   é aqui que mora a CONTINUIDADE)
4. ÂNCORAS DE PERSONAGEM (verbatim, completas, TODOS os planos — JUCA inteiro +
   TÉO inteiro + estado dele: "and a small white cloth bandage wrapped around
   his left thumb")
5. AÇÃO — 2–3 beats para 8s (3–4 para 10s), frases curtas sequenciais no
   presente, conectores "then/as/while/gradually", SEMPRE terminando em
   MOVIMENTO (nunca "freeze and stare")
6. "They do not speak and their mouths do not move."  (anti-lábio espúrio)
7. CÂMERA — UM trabalho por plano: "Static medium shot at puppet eye level,
   both characters in frame, movements flowing continuously from one task
   into the next."
8. NEGATIVOS fixos: "No text, no logos, no watermark, no anime eyes, no
   visible sclera, no teeth, no plastic gloss, no 2D vector look, no CGI
   Pixar look, no extra fingers."
```

## "Tem que ter os segundos?" — RESPOSTA DIRETA
- **No prompt: NÃO.** A duração NÃO vai no texto (o modelo não precisa; quem
  define o comprimento é o `video_length` no settings). Única exceção oficial:
  cortes multi-shot dentro de UMA geração (`"[Shot 2] At 00:04.500"`, provado no
  TESTE_02) — mas NOSSO formato usa 1 bloco de ação por geração, então não usamos.
- **No settings: SIM** — `video_length: "8s"` por plano.
- **A duração manda no número de beats: ~1 beat a cada 3s.** 8s = 2–3 beats;
  10s = 3–4. Mais que isso = movimento engasgado. Menos = plano morto.

## A fórmula da HISTÓRIA (nível episódio — TÉO & JUCA empresa faz-tudo)
1. **Cada episódio = 1 SERVIÇO**: objeto de cliente + etiqueta em branco no
   plano 1 (a semente da empresa; episódios independentes entre si).
2. **Cadeia causal obrigatória**: a falha do plano N é a CAUSA do plano N+1.
   (Nada de acontecidos aleatórios — a regra que você estabeleceu.)
3. **Estado muda NO CORTE** (técnica oficial "opening-state continuity"):
   bandagem, 2º prego, objeto reencostado — cada plano ABRE descrevendo o
   estado resultante do anterior. "Segments must be contiguous, no gaps" (HF).
4. **Callbacks plantados no SET**: a sobra da tábua aparece no plano 2 para
   salvar o plano 5; a escada cambaleia no 4 para cair no 6.
5. **Timing cômico** (o "Ar Cômico"): beat de silêncio ANTES da reação
   ("a long beat of complete silence") + reação física exagerada (braço
   vibrando) + silêncio de punchline. Também no soundscape.
6. **Gags por RESULTADO + REAÇÃO**, nunca por impacto exato (a IA não acerta
   contatos milimétricos; a reação + o estado do corte seguinte vendem o gag).
7. **Assinatura 1× por episódio** (aperto de mãos) — nunca por plano.
8. **Finais em movimento** (o único congelamento legítimo é o punchline final).
9. **Zero hand-offs de objetos pequenos entre personagens** dentro do plano
   (o lápis teleporta — lição A Cadeira). Cada um com suas ferramentas.
10. **Estrutura de 6 beats ≈ 50s**: Serviço → Tentativa → Falha (com causa) →
    Reação calma + Gambiarra → Novo caos → Resolução + Callback/Assinatura.

## Soundscape (regra mais contraintuitiva — e a mais medida)
**Eventos NOMEADOS e DISCRETOS = áudio audível.** Vago = silêncio.
- ✅ "A handsaw scrapes slowly, a wooden clatter as the plank slips, two soft
  wordless grunts, then a beat of complete silence" → medido −26 a −38 LUFS
- ❌ "A soft hum and low ambience" → medido **−47 a −inf LUFS** (piloto inteiro)
- Sem repetir diálogo (não temos) e sem música diegética: `non_diegetic_music: N/A`
  (trilha musical vai na pós, estilo Petr Skoumal, se quisermos).

## Anti-padrões (todos sofridos e medidos nesta série)
| Erro | Consequência medida |
|---|---|
| Terminar plano com "freeze and stare/nod" | todo plano vira mini-episódio parado (feedback onda 1) |
| Soundscape vago ("soft", "low", "faint") | −47 a −inf LUFS — silêncio digital |
| Hand-off de objeto pequeno no mesmo plano | objeto "teleporta" entre as mãos (lápis, A Cadeira) |
| Desastre sem motivação causal | "por que martelar areia?" — quebra a lógica (feedback) |
| Plano >15s (multi-janela) | crash CUTLASS na janela 2 (TESTE_03, 26 min perdidos) |
| Settings sem `activated_loras` | −60% de nitidez (censo metadata: 0/38 com LoRA) |
| Exigir impacto físico exato | IA erra o contato — usar resultado+reação |
| Contradizer câmera/estilo/ação | guia oficial: reduz consistência |
| >5 beats em 10s | movimento engasgado (critério de rejeição 7) |

## Fontes
1. Guia oficial do modelo: `C:\pinokio\api\wan2gp-amd\app\models\minimax_h3\prompt_enhancer.py`
   (formato, [Shot N] At MM:SS.mmm, <d>[Language], soundscape sem repetir diálogo,
   "speaking with natural lip movements synchronized")
2. Parser: `shared\utils\prompt_parser.py` (os 3 campos são estruturados)
3. Web (validação cruzada): PhotoGPT (fórmula STYLE+FRAMING+SUBJECT+ENV →
   OPENING-STATE CONTINUITY → SMALL NATURAL MOVEMENT → ACTION ONSET),
   HuggingFace MiniMax-H3 (segments contíguos, presente, "then/as/while",
   3–8 segmentos, ≤7000 chars), Fuser (ação como evento físico; UM movimento
   de câmera por plano; artefatos do meio vendem o estilo), Pixo (exemplo
   claymation confirma fingerprints/cadence).
4. Nosso banco: 3 testes originais + 18 planos TÉO&JUCA + Piloto B (38 clipes)
   — todos com metadata embutida, telemetria e gate v2.1.
