# -*- coding: utf-8 -*-
"""iniciar_smoke_60s.py — marca o START real da produção e roda o smoke 8/640.

Le EPISODIOS/_smoke_meta.json (gerado pelo teste_autoepisodio_60s.py), grava
smoke_timer.json com o instante do play e, ao terminar, grava o fim, o total e
o delta contra a meta de 1h37 (97 min). O vídeo final fica em
EPISODIOS/<slug>/<slug>_SMOKE60.mp4.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
APP = Path(__file__).resolve().parent
META = APP / "EPISODIOS" / "_smoke_meta.json"
TIMER = APP / "smoke_timer.json"
META_MIN = 97.0  # 1h37


def agora(t=None):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


if not META.exists():
    raise SystemExit("XX _smoke_meta.json ausente — gere o episódio primeiro.")

m = json.loads(META.read_text(encoding="utf-8"))
ep = Path(m.get("pasta") or (APP / "EPISODIOS" / m["slug"]))
print("=" * 78, flush=True)
print("EPISODIO:", m.get("slug"), "|", m.get("resumo"), flush=True)
print("PASTA:", ep, flush=True)
T0 = time.time()
print(">>> START DA PRODUCAO: %s" % agora(T0), flush=True)
print(">>> MODO: 8 steps / 1152x640 (setup aprovado) | meta 1h37 (97 min)", flush=True)
print("=" * 78, flush=True)
TIMER.write_text(json.dumps({"inicio": agora(T0), "t0": T0, "meta_min": META_MIN,
                             "slug": m.get("slug"), "modo": "8/640"},
                            ensure_ascii=False, indent=2), encoding="utf-8")

r = subprocess.run([PY, str(APP / "smoke_60s.py")])

T1 = time.time()
total = (T1 - T0) / 60.0
videos = sorted(ep.glob("*_SMOKE60.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
video = str(videos[0]) if videos else None
res = {"inicio": agora(T0), "fim": agora(T1), "total_min": round(total, 2),
       "meta_min": META_MIN, "delta_min": round(total - META_MIN, 2),
       "rc": r.returncode, "video": video, "slug": m.get("slug"), "modo": "8/640"}
TIMER.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("\n" + "=" * 78, flush=True)
print(">>> FIM DA PRODUCAO: %s" % agora(T1), flush=True)
print(">>> TOTAL: %.2f min (%.2f h) | meta 97 min | delta %+.2f min"
      % (total, total / 60.0, total - META_MIN), flush=True)
print(">>> VIDEO:", video or "NAO ENCONTRADO", flush=True)
print("=" * 78, flush=True)
sys.exit(r.returncode)
