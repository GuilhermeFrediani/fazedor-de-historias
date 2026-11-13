# P4 — PLANO DE ATIVAÇÃO E ROLLBACK DO VEDA SPARSE (proposta; NADA aplicado) — 18/10/2026

## 1. Estado atual (intocado e preservado)

- Configuração de produção validada: `minimax_h3_fl2va_pruned` + Profile 5 + GGUF Q4 +
  SDPA + Spectrum 6 passos + seed 7001 + `kernel_precision: "strict"` + watchdog v2
- Vídeos T1/T2/T3 aprovados e preservados (hashes no manifesto)
- Nenhuma alteração feita nesta missão P4 (somente leitura confirmada)

## 2. O que a ativação tocaria (se autorizada no futuro)

| Item | Ação | Reversível? |
|---|---|---|
| Settings da geração (novo arquivo, ex.: `test1_veda_settings.json`) | Trocar UMA chave: `model_type` → `minimax_h3_fl2va_pruned_veda` | ✓ 1 chave |
| Download automático na 1ª execução | Predictor `minimax_h3_t2va_veda_predictor_int8_convrot.safetensors` — **267 MB** (pior caso: também o bf16, +526 MB ⇒ ~793 MB). Transformador/VAEs/LoRA: **nada baixa** (mesmos arquivos já no disco — URLs idênticas no model def) | ✓ arquivos ficam; apagáveis |
| wgp_config.json | **NADA muda** (o handler trava `override_attention="veda"` sozinho para o modelo veda) | — |
| Código | **NADA muda** (integração in-tree no commit fde3c7e) — exceto se você optar pelo patch opcional do §4 | — |
| Watchdog v2 | NADA muda (continua ativo; Veda adiciona ~0,7–1,3 GB VRAM — coberto pelos limiares) | — |

**Custo operacional total:** download ≤793 MB • zero compilação (Triton JIT on-demand na
1ª execução, segundos) • +~0,7–1,3 GB VRAM de trabalho • zero dependências novas.

## 3. Procedimento de rollback (garantido e testado por construção)

1. Reverter `model_type` para `minimax_h3_fl2va_pruned` (1 chave) — **ambiente de
   produção volta exatamente ao estado validado** (T1/T2/T3 comprovadamente
   reproduzíveis: seed 7001 determinístico).
2. (Opcional) liberar disco: apagar `app\ckpts\minimax_h3\minimax_h3_t2va_veda_predictor_*.safetensors`
   (267–793 MB). Nada mais referencia esses arquivos no modo normal.
3. Nada é desinstalado; nada é reinstalado; o patch (se aplicado) reverte pelo backup.
**O rollback preserva 100% da instalação funcional** — o modelo veda é uma ENTRADA
alternativa de geração, não uma substituição de componentes.

## 4. OPÇÃO (não aplicada) — patch de 1 linha da launch config para HIP

**Contexto:** em `kernel_precision:"strict"` o WanGP usa `_launches[0] = (4, 3)` fixo;
o upstream mediu NA SUA GPU que (4 warps) é **6,5× mais lento** que (8, 3) em HIP
(hardware.md, registro RX 9060 XT). O patch alinha a config padrão à evidência da GPU exata.

```diff
--- app/models/minimax_h3/veda/sparse_int8.py  (commit fde3c7e, inalterado)
+++ app/models/minimax_h3/veda/sparse_int8.py  (proposto, se autorizado)
@@
-_launches = ((4, 3), (4, 2), (8, 3))
+_launches = ((8, 3), (4, 3), (4, 2))   # HIP: 8 warps obrigatório (medido na RX 9060 XT:
+                                       # 60,5 ms vs 391,7 ms no tune upstream; o modo
+                                       # fast/tuner já escolheria (8,3) por benchmark)
```

- **Efeito colateral:** nenhum para o modo atual (o arquivo só é importado por modelos
  veda; o pipeline pruned normal não passa por ele).
- **Backup/diff/rollback:** backup `sparse_int8.py.orig` + diff registrado em
  PATCHES_DIFF.md; rollback = restaurar o backup (1 arquivo).
- **Alternativa sem patch:** rodar o teste veda em `kernel_precision:"fast"` SOMENTE em
  janela única (o bug CUTLASS/fp16_conv3d só existe no VAE encode do overlap de janelas
  múltiplas; T1/T2 rodaram com fast sem problema) — conflita com a regra "preservar
  strict", portanto exige autorização explícita e NÃO seria usado em janelas múltiplas.

## 5. Plano de teste proposto (se autorizado; ordem e critérios)

1. **Pré:** definir a decisão do §4 (strict puro × patch × fast-só-janela-única).
2. **A/B de janela única (T1-equivalente):** mesmo prompt/seed 7001/6 passos/Spectrum/
   GGUF/Profile 5 — comparar: tempo/passo (base: 170 s medidos), VRAM/commit (watchdog
   log), decode/loudness, e SUA avaliação visual+auditiva lado a lado com o T1.
   - Critérios objetivos: passo ≥20% mais rápido (strict) OU ≥30% (patch); sem abort do
     watchdog; decode sem erros; loudness em faixa comparável; **áudio pt-BR aprovado por você**
   - Falha qualquer critério ⇒ rollback do §3 e resultado documentado como REPROVADO
3. **Só após aprovação do A/B:** teste de 2 janelas (T3-equivalente 18 s) para emenda +
   VAE encode (valida também a interação com strict no overlap).
4. **Só então:** extrapolar para 30–60 s e por fim 5 min (as projeções do
   P4_VEDA_FONTES_E_PERFORMANCE.md permanecem projeções até essas medições).

## 6. Guardrails mantidos

Watchdog v2 intocado • regras de parada da missão ativas • nenhuma geração
simultânea • sem retry automático • patch só com sua autorização • não usar `fast`
com janelas múltiplas (bug CUTLASS documentado) • sem image_start • 6 passos •
sem SageAttention como atenção geral.
