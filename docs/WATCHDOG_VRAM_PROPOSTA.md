# WATCHDOG DE VRAM — PROPOSTA (Fase 2 — sem execução, aguardando autorização)

## 1. Mecanismos de monitoramento EXISTENTES (inventário)

| Mecanismo | O que mede | Frequência | Enforcement | Estado |
|---|---|---|---|---|
| `gen_test.py` → `MemorySampler` (in-process) | torch `memory_allocated/reserved`, driver free (`mem_get_info`), margem de commit (`GlobalMemoryStatusEx`) | 5 s | **Aborta** se margem de commit < 5 GB em 2 amostras (cancel + exit 3 + marcador) | ATIVO nos 3 testes |
| `mem_sampler.ps1` (externo) | RAM disp., commit usado/limite/margem, GPU dedicada/compartilhada (contadores de performance) | 5–7 s | Nenhum (só registra) | usado na missão noturna; **parado** (não roda agora) |
| Eventos JSONL | fases, passos, streams, erros | contínuo | nenhum | ativo por geração |
| Resultado do job | erros Python/HIP capturados a posteriori | fim | nenhum | a posteriori |

**Lacunas comprovadas:** o critério "VRAM reservada > 15 GB" e "driver livre ≈ 0" da
missão NÃO têm enforcement (o Teste 3 ultrapassou ambos em 1 amostra — 16.050 MB /
0 MB — e o watchdog não agiu). Erros HIP não são vigiados em fluxo (só no fim).

## 2. PROPOSTA — MemorySampler v2 (diff sobre `gen_test.py`; nada aplicado)

```diff
--- gen_test.py (atual)
+++ gen_test.py (proposto)
 class MemorySampler(threading.Thread):
-    """Amostra memoria CUDA (torch) + commit do Windows a cada N segundos.
-    Watchdog da missao (secao 12): se a margem de commit ficar abaixo de 5120 MB em
-    2 amostras consecutivas, cancela o job e encerra o processo (gravando marcador)."""
+    """Amostra memoria CUDA (torch) + commit a cada N segundos.
+    Watchdog v2 — regras da missao (secao 12) COM diferenciação transitorio×persistente:
+      T1 (warn)  : qualquer amostra > limiar -> registra evento TRANSITORIO no CSV
+      T2 (abort) : limiar sustentado por K amostras consecutivas -> cancela + exit
+      T3 (abort imediato): condição extrema em 1 amostra -> cancela + exit
+    Limiares:
+      commit_margin      < 5120 MB  K=2                       (igual hoje)
+      vram_reserved      > 15360 MB K=3 ; imediato se > 15872 MB (15,5 GB)
+      driver_free        <  300 MB  K=3 ; imediato se <  50 MB
+      erro HIP/ROCm/OOM  detectado no stream de eventos      -> abort imediato
+    Justificativa dos K: pico transitório do T3 (16.050 MB / 0 MB) durou 1 amostra
+    (~5 s) sem consequência; condicao persistente por 15 s indica tendencia real
+    (vazamento/escalonamento) e e quando a missao manda interromper."""

     def __init__(self, out_csv, interval=5.0, job_holder=None, tag=""):
         ...
         self._margin_hits = 0
+        self._vram_hits = 0
+        self._driver_hits = 0
+        self._ev_f = None  # log de eventos do watchdog

     def run(self):
         import torch
         while not self.stop_flag.is_set():
             ...
             alloc = torch.cuda.memory_allocated(0) / (1024 * 1024)
             resv  = torch.cuda.memory_reserved(0) / (1024 * 1024)
             free_b, total_b = torch.cuda.mem_get_info(0)
+            driver_free = free_b / (1024 * 1024)
+            # ---- VRAM reserved (novo) ----
+            if resv > 15872:                      # >15,5 GB: abort imediato
+                self._abort(f"VRAM reservada {resv:.0f} MB > 15500 MB (1 amostra)")
+            if resv > 15360:                      # >15 GB: exige persistencia
+                self._vram_hits += 1
+                self._warn("VRAM_RESERVED", f"{resv:.0f} MB", self._vram_hits, K=3)
+                if self._vram_hits >= 3:
+                    self._abort(f"VRAM reservada > 15360 MB por 3 amostras (ult: {resv:.0f} MB)")
+            else:
+                self._vram_hits = 0
+            # ---- driver free (novo) ----
+            if driver_free < 50:
+                self._abort(f"driver free {driver_free:.0f} MB < 50 MB (1 amostra)")
+            if driver_free < 300:
+                self._driver_hits += 1
+                self._warn("DRIVER_FREE", f"{driver_free:.0f} MB", self._driver_hits, K=3)
+                if self._driver_hits >= 3:
+                    self._abort(f"driver free < 300 MB por 3 amostras (ult: {driver_free:.0f} MB)")
+            else:
+                self._driver_hits = 0
+            # ---- commit (existente, mantido) ----
             ...código atual de margin < 5120 MB com 2 hits...

+    # ---- detecção de erros HIP/OOM no fluxo de eventos (novo, no loop principal) ----
+    HIP_PATTERNS = ("hipError", "HIP error", "cudaError", "OutOfMemoryError",
+                    "device-side assert", "invalid device function")
+    # no laço de eventos, antes de ev_stream(...):
+    if event.kind == "stream" or event.kind == "error":
+        txt = str(getattr(event, "data", ""))
+        if any(p.lower() in txt.lower() for p in HIP_PATTERNS):
+            ev("watchdog_abort", {"motivo": "erro HIP/ROCm/OOM no fluxo", "trecho": txt[:200]})
+            job.cancel(); time.sleep(3); os._exit(4)
```

### Lógica de interrupção (resumo)

| Condição | 1ª amostra | Persistência exigida | Ação |
|---|---|---|---|
| Commit < 5 GB | warn | 2 amostras (10 s) | cancel + exit 3 |
| VRAM reservada > 15 GB | warn (TRANSITORIO no log) | 3 amostras (15 s) | cancel + exit 3 |
| VRAM reservada > 15,5 GB | — | imediata | cancel + exit 3 |
| Driver free < 300 MB | warn | 3 amostras (15 s) | cancel + exit 3 |
| Driver free < 50 MB | — | imediata | cancel + exit 3 |
| Erro HIP/OOM no fluxo | — | imediata | cancel + exit 4 |

**NaNs:** não são detectáveis externamente sem instrumentar tensores internos do modelo
(alteração de código de terceiros — fora do escopo autorizado). Mitigação praticável:
inspeção pós-geração (frames pretos/verdes na análise) — já parte do fluxo de entregáveis.
Documentado como limitação.

### Por que esses limiares

- **VRAM 15 GB / 15,5 GB**: regra da missão (15,0) com margem de 0,5 GB para abort
  imediato. **CORREÇÃO (pós-testes unitários, 18/10):** o pico real do T3 (16.050 MB)
  está ACIMA de 15,5 GB — pelas regras da missão é **abort crítico imediato**, e não
  "transitório" como esta proposta afirmou inicialmente. Um pico como o do T3
  interromperá a geração por design; a faixa transitória (warn, até 3 amostras) é
  15,36–15,87 GB.
- **Driver free 300/50 MB**: o T3 tocou 0 MB por 1 amostra sem falha (o pool reservado
  do PyTorch cobre o pico); 300 MB sustentados por 15 s = tendência real de exaustão.
- **K=3 (15 s)**: intervalo de amostragem de 5 s; 3 amostras consecutivas eliminam
  ruizinho transitório comprovadamente inofensivo, mantendo a regra da missão para
  condições persistentes.

## 3. PLANO DE VALIDAÇÃO (pós-autorização; nada executado agora)

1. **Teste de não-acionamento falso (14 min):** rerun do Teste 1 (perfil de carga
   conhecido: VRAM reservada pico 8,8 GB, driver ≥6,7 GB) → watchdog v2 NÃO deve abortar;
   CSV deve conter 0 eventos TRANSITORIO.
2. **Teste de classificação correta (31 min):** rerun do Teste 3 → o pico do VAE encode
   da J2 (16,05 GB / 0 MB por ~5 s) deve gerar eventos TRANSITORIO nos logs SEM aborto;
   geração deve completar.
3. **Teste de acionamento real (controlado, opcional):** geração curta com
   `--preload 12000` (empurra VRAM deliberadamente ao limite) → abort esperado por
   VRAM sustentada; verificar marcador + cancelamento limpo + preservação de logs.
4. Critérios de aceite: 100% dos aborts com marcador gravado; nenhum aborto sem
   condição persistente comprovada no CSV; gerações válidas inalteradas.

**Rollback:** o diff toca apenas `gen_test.py` (arquivo próprio da missão, backup
trivial por cópia; nenhum arquivo de terceiros). Aplicação só mediante sua autorização.
