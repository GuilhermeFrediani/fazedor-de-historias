"""Harness de geracao headless WanGP (MiniMax H3) com telemetria.

Uso:
    python gen_test.py --settings testX_settings.json --tag TESTE_01

O arquivo de settings e um overlay aplicado sobre os defaults do modelo.
Saídas (na pasta do script):
    <tag>_events.jsonl   - eventos com timestamps (download/load/progress/result)
    <tag>_mem.csv        - amostras de memoria torch (allocated/reserved/driver free)
    <tag>_summary.json   - resultado, tempos e erros
    <tag>_settings_effective.json - settings finais usados
"""
import argparse
import csv
import ctypes
import datetime as dt
import json
import os
import sys
import threading
import time
from pathlib import Path

APP_ROOT = Path(r"C:\pinokio\api\wan2gp-amd\app")
sys.path.insert(0, str(APP_ROOT))

_GIT = r"C:\pinokio\bin\miniforge\Library\ucrt64\bin\git.exe"
os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = _GIT
os.environ["PATH"] = r"C:\pinokio\bin\miniforge\Library\ucrt64\bin;" + os.environ.get("PATH", "")
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
# Alinha com o ENVIRONMENT do Pinokio (C:\pinokio\ENVIRONMENT)
os.environ.setdefault("HF_HOME", r"C:\pinokio\cache\HF_HOME")
os.environ.setdefault("TORCH_HOME", r"C:\pinokio\cache\TORCH_HOME")

from shared.api import init  # noqa: E402

TURBO_LORA_8STEP = "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/loras/minimax_h3_lightx2v_fl2v_turbo_8step_alpha8_v1.0_bf16.safetensors"

# ---------------------------------------------------------------------------
# Watchdog v2 (P2) — regras da missao com diferençia transitorio x persistente.
# IMPORTANTE: VRAM "reservada" (pool do alocador PyTorch) NAO e memória efetiva-
# mente ocupada por tensores vivos ("alocada"). Ambas sao registradas separada-
# mente no CSV, junto com a memória livre reportada pelo DRIVER e a margem de
# COMMIT do Windows. As decisões (motivo + valores) vão para <tag>_watchdog.jsonl.
# ---------------------------------------------------------------------------
WATCHDOG_LIMITS = {
    "commit_abort_mb": 5120,    # margem de commit < 5 GB (regra da missão)
    "commit_hits": 2,           # por 2 amostras consecutivas
    "vram_abort_mb": 15360,     # VRAM reservada > 15 GB (regra da missão)
    "vram_hits": 3,             # por 3 amostras consecutivas de 5 s (persistente)
    "vram_critical_mb": 15872,  # > 15,5 GB: crítica imediata (1 amostra)
    "driver_abort_mb": 300,     # driver livre < 300 MB: persistente (3 amostras)
    "driver_hits": 3,           # por 3 amostras consecutivas
    "driver_critical_mb": 50,   # driver livre < 50 MB: crítica imediata
}

# Padrões fatais que abortam imediatamente (sem esperar amostras), no fluxo de eventos.
# Todos já normalizados (minúsculo, sem espaços/underscores) — a mesma normalização
# aplicada ao texto em _hip_fatal().
HIP_FATAL_PATTERNS = (
    "hiperror", "cudaerror", "outofmemoryerror", "device-sideassert",
    "illegalmemoryaccess", "invaliddevicefunction", "hipruntimeerror",
)


def watchdog_decide(margin, resv, driver_free, hits):
    """Decisão pura do watchdog (sem efeitos colaterais — testável unitariamente).

    Entradas por amostra (MB, podem ser None se a leitura falhar) e o dict de
    contadores `hits` (mutado em lugar). Retorna (acao, motivo) onde acao ∈
    {"ok", "warn", "abort"}. Ordem: críticas imediatas primeiro, depois os
    limiares persistentes (commit → VRAM reservada → driver livre).
    """
    # --- críticas imediatas (1 amostra) ---
    if resv is not None and resv > WATCHDOG_LIMITS["vram_critical_mb"]:
        hits.update(vram=WATCHDOG_LIMITS["vram_hits"])
        return "abort", (f"CRITICA IMEDIATA: VRAM reservada {resv:.0f} MB > "
                         f"{WATCHDOG_LIMITS['vram_critical_mb']} MB em 1 amostra")
    if driver_free is not None and driver_free < WATCHDOG_LIMITS["driver_critical_mb"]:
        hits.update(driver=WATCHDOG_LIMITS["driver_hits"])
        return "abort", (f"CRITICA IMEDIATA: driver livre {driver_free:.0f} MB < "
                         f"{WATCHDOG_LIMITS['driver_critical_mb']} MB em 1 amostra")
    # --- persistentes: VRAM reservada > 15 GB por 3 amostras ---
    if resv is not None and resv > WATCHDOG_LIMITS["vram_abort_mb"]:
        hits["vram"] = hits.get("vram", 0) + 1
        if hits["vram"] >= WATCHDOG_LIMITS["vram_hits"]:
            return "abort", (f"VRAM reservada > {WATCHDOG_LIMITS['vram_abort_mb']} MB por "
                             f"{hits['vram']} amostras consecutivas (ult: {resv:.0f} MB)")
        return "warn", (f"TRANSITORIO vram_reservada={resv:.0f} MB "
                        f"(amostra {hits['vram']}/{WATCHDOG_LIMITS['vram_hits']})")
    hits["vram"] = 0
    # --- persistentes: driver livre < 300 MB por 3 amostras ---
    if driver_free is not None and driver_free < WATCHDOG_LIMITS["driver_abort_mb"]:
        hits["driver"] = hits.get("driver", 0) + 1
        if hits["driver"] >= WATCHDOG_LIMITS["driver_hits"]:
            return "abort", (f"driver livre < {WATCHDOG_LIMITS['driver_abort_mb']} MB por "
                             f"{hits['driver']} amostras consecutivas (ult: {driver_free:.0f} MB)")
        return "warn", (f"TRANSITORIO driver_livre={driver_free:.0f} MB "
                        f"(amostra {hits['driver']}/{WATCHDOG_LIMITS['driver_hits']})")
    hits["driver"] = 0
    # --- persistentes: margem de commit < 5 GB por 2 amostras ---
    if margin is not None and margin < WATCHDOG_LIMITS["commit_abort_mb"]:
        hits["commit"] = hits.get("commit", 0) + 1
        if hits["commit"] >= WATCHDOG_LIMITS["commit_hits"]:
            return "abort", (f"margem de commit {margin:.0f} MB < "
                             f"{WATCHDOG_LIMITS['commit_abort_mb']} MB por "
                             f"{hits['commit']} amostras consecutivas")
        return "warn", (f"TRANSITORIO margem_commit={margin:.0f} MB "
                        f"(amostra {hits['commit']}/{WATCHDOG_LIMITS['commit_hits']})")
    hits["commit"] = 0
    return "ok", ""


def _hip_fatal(text):
    """True se o texto de stream/erro casa um padrão HIP/ROCm fatal (abort imediato)."""
    low = str(text).lower().replace(" ", "").replace("_", "")
    return any(p in low for p in HIP_FATAL_PATTERNS)


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


class MemorySampler(threading.Thread):
    """Amostra memoria CUDA (torch) + commit do Windows a cada N segundos.

    Watchdog da missao (secao 12): se a margem de commit ficar abaixo de 5120 MB em
    2 amostras consecutivas, cancela o job e encerra o processo (gravando marcador).
    """

    def __init__(self, out_csv: Path, interval=5.0, job_holder=None, tag=""):
        super().__init__(daemon=True)
        self.out_csv = out_csv
        self.interval = interval
        self.job_holder = job_holder if job_holder is not None else {}
        self.tag = tag
        self.stop_flag = threading.Event()
        self._f = open(out_csv, "w", newline="", encoding="utf-8")
        self._w = csv.writer(self._f)
        self._w.writerow(["timestamp", "phase", "mem_allocated_mb", "mem_reserved_mb",
                         "driver_free_mb", "driver_total_mb", "commit_margin_mb"])

    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    @classmethod
    def commit_margin_mb(cls):
        stat = cls._MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(cls._MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            avail = stat.ullAvailPageFile  # commit disponivel (aprox. margem de commit)
            used_limit_gap = stat.ullTotalPageFile - stat.ullAvailPageFile
            return int(avail / (1024 * 1024))
        return None

    def run(self):
        import torch
        wlog_path = self.out_csv.parent / f"{self.tag}_watchdog.jsonl"
        wlog = open(wlog_path, "a", encoding="utf-8")
        hits = {"commit": 0, "vram": 0, "driver": 0}

        def wlog_event(kind, motivo, margin, resv, driver_free):
            wlog.write(json.dumps({
                "t": now_iso(), "acao": kind, "motivo": motivo,
                "vram_reservada_mb": None if resv is None else round(resv, 1),
                "vram_alocada_mb": getattr(wlog_event, "_alloc", None),
                "driver_livre_mb": None if driver_free is None else round(driver_free, 1),
                "margem_commit_mb": margin, "fase": CURRENT_PHASE[0],
            }, ensure_ascii=False) + "\n")
            wlog.flush()

        while not self.stop_flag.is_set():
            margin = alloc = resv = driver_free = None
            try:
                margin = self.commit_margin_mb()
            except Exception:
                pass
            try:
                alloc = torch.cuda.memory_allocated(0) / (1024 * 1024)
                resv = torch.cuda.memory_reserved(0) / (1024 * 1024)
                free_b, total_b = torch.cuda.mem_get_info(0)
                driver_free = free_b / (1024 * 1024)
                self._w.writerow([now_iso(), CURRENT_PHASE[0],
                                  round(alloc, 1), round(resv, 1),
                                  round(driver_free, 1),
                                  round(total_b / (1024 * 1024), 1), margin])
                self._f.flush()
            except Exception as exc:  # nao derrubar a geracao por falha de amostra
                self._w.writerow([now_iso(), CURRENT_PHASE[0], f"ERRO: {exc}", "", "", "", margin])
            wlog_event._alloc = None if alloc is None else round(alloc, 1)
            # Watchdog v2: decisao pura (transitorio x persistente x critico)
            acao, motivo = watchdog_decide(margin, resv, driver_free, hits)
            if acao == "warn":
                wlog_event("TRANSITORIO", motivo, margin, resv, driver_free)
            elif acao == "abort":
                wlog_event("ABORT", motivo, margin, resv, driver_free)
                marker = self.out_csv.parent / f"{self.tag}_ABORT_WATCHDOG.txt"
                marker.write_text(
                    f"{now_iso()} motivo: {motivo}\nfase: {CURRENT_PHASE[0]}\n"
                    f"vram_reservada={resv} MB | driver_livre={driver_free} MB | "
                    f"margem_commit={margin} MB\n", encoding="utf-8")
                try:
                    job = self.job_holder.get("job")
                    if job is not None and not job.done:
                        job.cancel()
                except Exception:
                    pass
                time.sleep(3)
                os._exit(3)
            self.stop_flag.wait(self.interval)
        wlog.close()


CURRENT_PHASE = ["init"]


def parse_extra_args(cli_list):
    """Aplica overrides de CLI vindos do settings overlay (chave _cli_extra)."""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--no-lora", action="store_true", help="desativa o LoRA turbo")
    parser.add_argument("--steps", type=int, default=None)
    args = parser.parse_args()

    here = Path(__file__).parent
    events_path = here / f"{args.tag}_events.jsonl"
    mem_path = here / f"{args.tag}_mem.csv"
    summary_path = here / f"{args.tag}_summary.json"
    eff_path = here / f"{args.tag}_settings_effective.json"

    ev_f = open(events_path, "w", encoding="utf-8")

    def ev(kind, data):
        rec = {"t": now_iso(), "kind": kind, "data": data}
        ev_f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        ev_f.flush()
        # NUNCA print(): o console-capture transformaria isto em novos eventos stream (loop)

    MARKERS = ("download", "loading", "load", "error", "warning", "failed", "success",
               "vram", "ram", "%", "step", "window", "lora", "int8", "torch", "model",
               "saving", "saved", "generate", "audio", "video", "decode", "encode",
               "spectrum", "veda", "attention", "sparse")
    last_stream = {"text": None, "t": 0.0}

    def ev_stream(text):
        # filtra ruido e auto-eco; throttle de 2s; ignora barras de progresso repetidas.
        # Auto-eco do harness antigo = cadeias ANINHADAS ("[stream] ..." ou multiplos
        # "[stdout]"); prints legítimos do WanGP no stdout têm UM prefixo e sao mantidos
        # (necessario para capturar o print de ativacao do Veda — prova do kernel).
        if not text:
            return
        s = str(text)
        if "[stream]" in s or s.count("[stdout]") > 1 or s.count("[stderr]") > 1:
            return
        low = s.lower()
        if not any(m in low for m in MARKERS):
            return
        now = time.time()
        if s == last_stream["text"] and now - last_stream["t"] < 2.0:
            return
        last_stream["text"] = s
        last_stream["t"] = now
        ev("stream", s[:400])

    overlay = json.loads(Path(args.settings).read_text(encoding="utf-8"))
    model_type = overlay.get("model_type", "minimax_h3_fl2va_pruned")
    cli_extra = overlay.get("_cli_extra", [])  # ex: ["--perc-reserved-mem-max", "0.25"]

    t0 = time.time()
    ev("start", {"tag": args.tag, "model_type": model_type, "settings": overlay})

    CURRENT_PHASE[0] = "init_session"
    cli_base = ["--attention", "sdpa", "--profile", "5"] + cli_extra
    if overlay.get("_preload_mb") is not None:
        cli_base += ["--preload", str(int(overlay["_preload_mb"]))]
    session = init(
        root=APP_ROOT,
        cli_args=cli_base,
        console_output=False,
    )

    settings = dict(session.get_default_settings(model_type))
    ev("defaults_loaded", {"keys": len(settings)})

    # Aplica overlay (chaves iniciadas com "_" sao metadados/CLI, nao settings)
    for k, v in overlay.items():
        if k == "model_type" or k.startswith("_"):
            continue
        settings[k] = v

    if not args.no_lora and "activated_loras" not in overlay:
        settings["activated_loras"] = [TURBO_LORA_8STEP]
        settings["loras_multipliers"] = "1.0"
    if args.steps is not None:
        settings["num_inference_steps"] = args.steps

    eff_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False, default=str),
                        encoding="utf-8")
    ev("settings_ready", {"steps": settings.get("num_inference_steps"),
                          "resolution": settings.get("resolution"),
                          "seed": settings.get("seed"),
                          "lora": settings.get("activated_loras"),
                          "video_length": settings.get("video_length")})

    job_holder = {}
    sampler = MemorySampler(mem_path, job_holder=job_holder, tag=args.tag)
    sampler.start()

    CURRENT_PHASE[0] = "submit"
    t_submit = time.time()
    job = session.submit_task(settings)
    job_holder["job"] = job
    ev("submitted", {"elapsed_since_start_s": round(time.time() - t0, 1)})

    result = None
    last_progress = None
    try:
        while True:
            for event in job.events.iter(timeout=1.0):
                if event.kind == "progress":
                    p = event.data
                    key = (getattr(p, "phase", None), getattr(p, "current_step", None))
                    if key != last_progress:
                        last_progress = key
                        ev("progress", {"phase": getattr(p, "phase", None),
                                        "progress": getattr(p, "progress", None),
                                        "current_step": getattr(p, "current_step", None),
                                        "total_steps": getattr(p, "total_steps", None),
                                        "status": getattr(p, "status", None)})
                        CURRENT_PHASE[0] = str(getattr(p, "phase", "gen") or "gen")
                elif event.kind == "stream":
                    line = event.data
                    txt = f"[{getattr(line, 'stream', '')}] {getattr(line, 'text', '')}"
                    if _hip_fatal(txt):
                        ev("watchdog_abort", {"motivo": "padrao HIP/ROCm fatal no fluxo",
                                              "trecho": txt[:200]})
                        try:
                            job.cancel()
                        except Exception:
                            pass
                        time.sleep(3)
                        os._exit(4)
                    ev_stream(txt)
                elif event.kind == "error":
                    msg = str(getattr(event, "data", ""))
                    if _hip_fatal(msg):
                        ev("watchdog_abort", {"motivo": "padrao HIP/ROCm fatal em evento error",
                                              "trecho": msg[:200]})
                        try:
                            job.cancel()
                        except Exception:
                            pass
                        time.sleep(3)
                        os._exit(4)
                    ev("error", getattr(event, "data", None))
                elif event.kind == "preview":
                    pass  # previews nao interessam para o log
                elif event.kind == "output":
                    ev("output", getattr(event, "data", None))
                elif event.kind == "status":
                    ev("status", getattr(event, "data", None))
                else:
                    ev(event.kind, getattr(event, "data", None))
            if job.done:
                break
    except KeyboardInterrupt:
        job.cancel()
        ev("cancelled", {"reason": "KeyboardInterrupt"})
    finally:
        result = job.result()

    sampler.stop_flag.set()
    sampler.join(timeout=10)

    t_end = time.time()
    CURRENT_PHASE[0] = "done"
    summary = {
        "tag": args.tag,
        "success": bool(getattr(result, "success", False)),
        "generated_files": [str(p) for p in getattr(result, "generated_files", []) or []],
        "errors": [str(e) for e in getattr(result, "errors", []) or []],
        "cancelled": getattr(result, "cancelled", None),
        "elapsed_total_s": round(t_end - t0, 1),
        "elapsed_submit_to_done_s": round(t_end - t_submit, 1),
        "finished_at": now_iso(),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    ev("summary", summary)
    ev_f.close()
    with open(here / f"{args.tag}_done.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
