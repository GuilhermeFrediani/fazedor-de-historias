# VEDA — PLANO OPERACIONAL DO TESTE A/B (T0 → T1) — 19/10/2026

**Status: PROPOSTA — aguardando sua autorização (portão T0). Nada foi executado.**

## 0. Inspeção concluída (fatos verificados agora)

| Verificação | Resultado |
|---|---|
| 3 relatórios P4 | ✓ existem e conferem com o manifesto (hashes ok) |
| `gen_test.py` (watchdog v2) | ✓ `F1A2E714…` (inalterado desde P2+P3) |
| `wgp_config.json` | ✓ `7862EFD1…` — `strict` mantido, preload ausente |
| `sparse_int8.py` (veda) | ✓ `F52FD796…` ORIGINAL — **sem patch** (`_launches = ((4,3), (4,2), (8,3))` confirmado) |
| Predictor veda no disco | ✗ ausente — **será baixado (267 MB) na 1ª execução do braço B** |
| Pasta PILOTO_B | não existe (será criada; nenhum arquivo sobrescrito) |

## 1. Chave exata que habilita o Veda (mecanismo oficial)

- **Única chave**: `model_type: "minimax_h3_fl2va_pruned_veda"` nas settings de geração.
- O model def carrega `"veda": true` e `"override_attention": "veda"`; o handler
  (`minimax_h3_handler.py:864`) força `inputs["override_attention"] = "veda"` sozinho —
  **não há chave extra** e `wgp_config.json` não muda.
- Sequência interna: submit → override aplicado → `wgp.py:7304` grava
  `offload.shared_state["_attention"] = "veda"` → `VedaPolicy.begin_forward`
  (`veda/attention.py:128`) habilita → monta layouts por plano de tiles → imprime
  confirmação → `attend()` usa o kernel Triton INT8 esparso.
- `kernel_precision: "strict"` (mantido): o kernel esparso **roda**; apenas o auto-tuner
  de launch config é desligado, fixando `_launches[0] = (4 warps, 3 stages)` — a config
  que o upstream mediu 6,5× mais lenta na nossa GPU. **Comportamento esperado: Veda
  funcional, com ganho atenuado** (projeção P4: atenção ~1,8–2,4×; passo ~1,4–1,6×).

## 2. Evidência de que o kernel Veda rodou (sem fallback silencioso)

Prova primária — **o print de ativação** (só executa se `enabled=True`):
```
[MiniMax H3] Veda Triton Attention - 10% sparse, references ...; {how}
```
- `describe()` retorna `"X% sparse"` → contém `%` → **passa pelo filtro do meu
  `ev_stream`** e será capturado em `VEDA_B_events.jsonl` (verificado no código).
- `how` informa se o grid 1152×640 usou plano exato ou "nearest plan" (estamos fora do
  treino — o texto dirá).
- **Se o print NÃO aparecer** → o override não foi aplicado (atenção SDPA convencional
  silenciosa) → teste classificado **INCONCLUSIVO** conforme seus critérios (não
  apresentado como A/B válido).
Evidências corroborativas: (a) tempo por passo-âncora (atenção ≈63–64% do passo; queda
esperada de ~28–37% em strict — passo inalterado ≈ Veda inativo); (b) eventos de erro
(ValueError de gate, falha de compilação Triton) seriam **ruidosos**, não silenciosos.

## 3. Desenho do teste (menor amostra representativa)

**Amostra:** o próprio clipe do Teste 1 — 10 s, janela única, 243 frames, seed 7001,
prompt da cozinha com fala pt-BR ("Bom dia! O café de hoje ficou perfeito.").
Racional: é o pipeline real (T2VA vídeo+áudio), a menor duração que mede atenção
(difusão), memória e qualidade de imagem **e áudio/fala** na mesma execução — sem custo
extra de "sequência completa para validar áudio". Janela única evita variáveis extras
(VAE encode de overlap) na 1ª medição.

| Braço | Config | Diferenças exatas vs. produção |
|---|---|---|
| **A — referência** | `test1_settings.json` EXATAMENTE como está | NENHUMA (execução nova do baseline atual: strict + watchdog v2, sem preload) |
| **B — Veda** | novo `test1_veda_settings.json` (cópia com diff verificado) | **2 chaves**: `model_type` → veda; `output_filename` → `teste_01_veda` (preservar vídeos existentes). Resto byte-idêntico |

**Arquivos alterados/criados:** somente o settings novo do braço B (+predictor baixado
pelo próprio WanGP em `app\ckpts\minimax_h3\`, 267 MB). **Nada** do pipeline é tocado.
Baseline alternativo dispensável: T1 (846 s) e P3 (836 s) medem ~170 s/passo e servem de
referência histórica — mas recomendo o A novo para eliminar qualquer confundidor
(P3 usava preload 6000; T1 rodou com `fast`).

## 4. Procedimento (comandos exatos, se autorizado)

```powershell
cd "C:\Users\Guilherme\Documents\Projeto Padrão"
# A — referência (~14 min)
& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" gen_test.py --settings test1_settings.json --tag VEDA_A
# B — Veda (~14 min + download 267 MB na 1ª vez)
& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" gen_test.py --settings test1_veda_settings.json --tag VEDA_B
# Análise dos dois arquivos
& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" analyze_video.py <videoA> <pastaA>
& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" analyze_video.py <videoB> <pastaB>
```

**Riscos por etapa:** A = nenhum (config já validada). B = (i) download 267 MB
(reversível); (ii) gate recusa (não esperado — capability (12,0) medida); (iii) kernel
Triton não compila no triton 3.7.1 → **falha ruidosa** documentada como resultado
(REJEITADO nesta config / INCONCLUSIVO), sem retry automático; (iv) +0,7–1,3 GB VRAM →
watchdog v2 cobre (limites de VRAM/commit/driver ativos).

## 5. Métricas e critérios

**Medições:** tempo/passo-âncora, difusão, encode/decode/áudio, total; VRAM
alocada/reservada/driver livre; margem de commit; eventos do watchdog
(`<tag>_watchdog.jsonl`); print de ativação; erros HIP/NaN; integridade, duração,
loudness EBU R128 e estrutura de silêncio/fala; frames 0/25/50/75/100% + folha de
contato para sua avaliação visual.

**Critérios de interrupção:** os do watchdog v2 (commit <5 GB×2; VRAM >15 GB×3 / >15,5
GB×1; driver <300 MB×3 / <50 MB×1; HIP fatal imediato) — **nenhuma proteção desativada**.

**Critérios de decisão (Fase T3):**
| Resultado | Critério objetivo |
|---|---|
| APROVADO COM STRICT | Print Veda presente + difusão **≥25% mais rápida** que A + sem abort/NaN/HIP + integridade OK + loudness ±2 LU de A + fala presente na janela esperada (+ sua aprovação visual/auditiva) |
| PATCH JUSTIFICADO (portão T2) | Print presente, kernel estável, **mas** ganho 15–25% (faixa consistente com a penalidade 4-warp) → evidência coletada → diff/rollback reapresentados → aplicar só com sua autorização explícita |
| REJEITADO NESTA CONFIG | Ganho <15%, OU qualquer abort/NaN/falha, OU degradação (integridade/loudness/fala) |
| INCONCLUSIVO | Print ausente (fallback silencioso) OU variável incontrolável |

## 6. Rollback (verificado antes do teste — nada a restaurar no pipeline)

1. Restaurar B = apagar `test1_veda_settings.json` (arquivo novo) — produção intacta.
2. (Opcional) liberar 267 MB: apagar `minimax_h3_t2va_veda_predictor_int8_convrot.safetensors`.
3. Conferência pós-teste: hashes de `gen_test.py`/`wgp_config.json`/`sparse_int8.py`
   inalterados + vídeo/relatórios T1/T2/T3/P3 intactos.
**O rollback preserva 100% da instalação funcional** (o modelo veda é entrada
alternativa, não substituição).

## 7. Patch de warps (bloqueado — pré-condições pendentes)

Diff já apresentado (P4_VEDA_PLANO_ROLLBACK §4). Só entra em pauta SE o braço B
demonstrar a penalidade (ganho 15–25%). Requisitos acumulados: evidência do A/B ✓ +
sua autorização explícita + backup `sparse_int8.py.orig` + re-teste controlado idêntico.

## 8. Fora de escopo (bloqueado nesta fase)

Geração longa (30–60 s ou 5 min) • patch de warps • `kernel_precision:"fast"` • preload
(nunca) • instalações/atualizações • qualquer alteração no watchdog ou no pipeline.
