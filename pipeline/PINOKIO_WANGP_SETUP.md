# PIPELINE — Setup Pinokio + WanGP (MiniMax H3)

Configuração EXATA da máquina que renderiza os clipes de TÉO & JUCA.
O Pinokio em si é um instalador de terceiros (~GBs, não versionado aqui) —
este documento reproduz toda a configuração necessária para reproduzir o ambiente.

## 1. Onde as coisas vivem

```
C:\pinokio\api\wan2gp-amd\app\          ← install do WanGP (Wan2GP)
   env\Scripts\python.exe               ← python do ambiente (3.12, usa o venv)
   outputs\                             ← TODOS os MP4 renderizados nascem aqui
C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py   ← harness de render por clipe
..\fazedor de histórias\fazedor_app\    ← o gerador (servidor + UI)
```

## 2. Modelo e receita de render (settings por clipe)

| Campo | Valor |
|---|---|
| `model_type` | `minimax_h3_fl2va_pruned` |
| `num_inference_steps` | 6 (turbo LoRA) |
| `resolution` | `1152x640` |
| `force_fps` | 24 |
| `video_length` | `"10s"` → 243 frames |
| `seed` | 7001 (identidade estável dos bonecos) |
| `guidance_scale` | 1 |
| `flow_shift` | 12 |
| `skip_steps_cache_type` | `spectrum` |
| `activated_loras` | `minimax_h3_lightx2v_fl2v_turbo_8step_alpha8_v1.0_bf16` (multiplier 1.0) |
| `config` | `gguf_q4_k_m` |
| `_cli_extra` | `["--profile","5"]` |

Template completo: `pipeline/template_settings_minimax_h3.json`.
Tempo medido: **~14,7 min por clipe de 10 s** (~88 s por segundo de vídeo).

## 3. Como o harness chama o WanGP

```
python gen_test.py --settings <arquivo>_settings.json --tag <TAG>
```

- gen_test conversa com a API do WanGP (mesma porta do app Pinokio),
- dispara a geração com o settings JSON,
- espera o MP4 nascer em `C:\pinokio\api\wan2gp-amd\app\outputs\<nome>.mp4`,
- grava artefatos ao lado do settings (`<TAG>_summary.json`, events, mem.csv).

Cadeia de episódio: rodar gen_test por clipe em sequência e concatenar com
ffmpeg (`-f concat -safe 0 -c copy`) — ver `fazedor_app/fumaca_v3.py` para o exemplo completo.

## 4. Limites descobertos na prática

- Clipe **≤ 10 s é confiável**; clipes mais longos travam no CUTLASS.
- **25 cenas** por clipe é o teto prático (mais que isso: congelamentos).
- Prompts > ~4.500 chars degradam a leitura da ação (v3 usa ~2.500).
- Ação DEVE ser a primeira instrução do prompt; âncoras visuais curtas no meio.
- Todo clipe termina **em movimento** (sem freeze/fade) — o modelo cola o último frame.

## 5. Áudio

O MiniMax H3 gera áudio diegético a partir do `overall_soundscape`
(3–5 eventos nomeados: material + verbo). `non_diegetic_music` = `N/A` (regra da série).
Sons de boca não-verbais (resfôlego, suspiro, estalo) são nomeados no soundscape.

## 6. ENCADEAMENTO VISUAL — CONFIRMADO EM A/B (14/nov/2026)

O H3 FL2VA aceita start/end frames NATIVAMENTE na nossa build
(`image_prompt_types_allowed: "TSEVL"`, `end_frames_always_enabled: True` no handler).

Chaves (settings JSON): `"image_start": "<caminho png>"`, `"image_end": "<caminho png>"`,
`"image_prompt_type": "S"` (só início) ou `"SE"` (ponte). O guia oficial pede a linha de
alinhamento no fim do prompt: *"For the target video, at 0.00 seconds into the target video,
<Picture 1> (from [Shot 1]) is fully referenced."*

**Prova medida (clipe 2, mesmo seed 7001):**
- controle (texto puro): 1º frame vs âncora = PSNR 10,3 dB (cena inventada)
- `image_start`: PSNR 26,8 dB — o clipe NASCE do frame pinado ✓
- `image_start` + `image_end` (ponte): início 25,9 dB ✓ e o último frame cai no
  estado pinado (27,4 dB vs a referência de fim) ✓

**As 3 lições do A/B (custaram 2 renders, valem a série):**
1. O keyframe de FIM deve ser um EDIT do frame de INÍCIO (mesma câmera, mesmos
   bonecos, só o estado muda). Usar o último frame de OUTRO render como fim
   produz um morph entre composições diferentes (câmera salta).
2. A cadeia PROPAGA DEFECTOS: o personagem extra alucinado no clipe 1 entrou
   na âncora e contamina o clipe 2. Regra: só encadeia a partir de clipe
   APROVADO pelo gate de visão (ou âncora limpa na mão).
3. Com imagem pinada, o texto AT START vira redundante (o pixel É o estado);
   o gate deve julgar a âncora ANTES do render, não o texto depois.
