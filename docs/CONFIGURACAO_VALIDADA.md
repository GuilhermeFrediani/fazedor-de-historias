# CONFIGURAÇÃO VALIDADA — Base de teste (FASE C)

**Data:** 18/10/2026 — valores confirmados por inspeção do código/clonagem + probe da API.

## Mapeamento: configuração de referência (antiga) → v18.17 atual

| Item de referência | Situação no v18.17 (evidência) | Decisão |
|---|---|---|
| MiniMax H3 FL2VA | Modelos: `minimax_h3_fl2va` (33B) e **`minimax_h3_fl2va_pruned` (20B)** | **Pruned 20B** (RAM 16 GB é o limite físico; 33B INT8 ≈ 33 GB não cabe; Pruned usa os mesmos settings) |
| Transformer INT8 | `transformer_quantization: "int8"` no wgp_config.json (auto); INT8 ConvRot pruned baixável (`MiniMax-H3-FL2VA-pruned_rank8_int8_convrot.safetensors`) | Mantido INT8 ✓ |
| Resolução 1152×640 | `resolution` aceita valores no grid VAE (bloco 32: 1152=36×32, 640=20×32) ✓ | "1152x640" |
| 24 fps | `force_fps: 24` | Mantido |
| RIFE ×2 → 48 fps | `temporal_upsampling` (pós-processamento; RIFE v4.26 integrado) | Validar APÓS geração nativa (regra da missão) |
| 6 passos | `num_inference_steps: 6` | Mantido |
| LoRA turbo 8 passos | Perfil **"Turbo Lightx2v FL2V 8 Steps v1.0"** existe (`profiles\minimax_h3_fl2va\`): LoRA `minimax_h3_lightx2v_fl2v_turbo_8step_alpha8_v1.0_bf16.safetensors`, steps 8, guidance 1, flow_shift 12 | Aplicar LoRA com **6 passos** (conforme referência) e guidance 1 / flow_shift 12 |
| SDPA | `--attention sdpa` disponível; SDPA usa AOTriton flash kernels no RDNA4 | `--attention sdpa` nos testes |
| T-FUSE | **Não existe no v18.17** (recurso da versão antiga; não encontrado no código) | Documentado como indisponível; sem substituição forçada |
| Spectrum | **Existe**: "Spectrum Feature Forecasting" = `skip_steps_cache_type: "spectrum"` (default start 25%, multiplier 0.08) | Ativar nos 3 testes (referência: ~2 passos pulados em 6) |
| Seed 7001 | `seed: 7001` | Mantido em todos os testes |
| Preload 6000 | `--preload 6000` (MB, preload manual de VRAM) | Mantido via CLI |
| Export H.264/AAC | WanGP exporta MP4 H.264/AAC por padrão (imageio-ffmpeg 9.0.2 + codec config) | Verificar no arquivo gerado |
| SageAttention | Missão: NÃO ativar (foi ~49% mais lento/passso) | SDPA only; sageattention nem instalado |

## Configuração efetiva dos testes (base comum)

- Modelo: `minimax_h3_fl2va_pruned` (T2VA: texto → vídeo+áudio integrados)
- attn: SDPA; profile: 4 (MMGP); preload: 6000 MB; vram-allocator: vmm_spill (default)
- INT8: transformer + text encoder (int8); kernels: auto (Triton ativo — evidência no log)
- Passos: 6; LoRA turbo 8-step v1.0 @ 1.0; guidance 1; flow_shift 12; solver euler
- Spectrum: on (defaults 25% / 0.08)
- Res: 1152×640; fps: 24; seed: 7001
- Prompt: formato oficial MiniMax H3 (T2VA) com `<d>[Portuguese] ...</d>` para fala pt-BR

## Ferramenta de automação (workspace)

- `gen_test.py` — geração headless via `shared.api.init` com telemetria (mem torch: alocada/reservada/driver; eventos com timestamps; tempos por fase)
- `mem_sampler.ps1` — amostrador de sistema (RAM, commit usado/limite/margem, VRAM dedicada/compartilhada) a cada 5 s
- Settings por teste: `testN_settings.json` (overlay sobre defaults do modelo)
