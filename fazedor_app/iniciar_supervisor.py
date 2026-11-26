# -*- coding: utf-8 -*-
"""iniciar_supervisor.py — lança o render_supervisor.py DESTACADO da sessão.

Um restart do servidor do agente não mata o supervisor nem o render. Use:

  python iniciar_supervisor.py --slug a-sujeira-mudou-de-andar
  python iniciar_supervisor.py --attach-pid 10156 --since "2026-11-26 13:15:10"

Depois:
  python render_supervisor.py --status
  echo stop > EPISODIOS/<slug>/automation/STOP
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
APP = Path(__file__).resolve().parent
EPIS = APP / "EPISODIOS"
CFG = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--attach-pid", type=int, default=0)
    ap.add_argument("--since", default="")
    ap.add_argument("--max-restarts", type=int, default=10)
    ap.add_argument("--stale-min", type=float, default=45.0)
    a = ap.parse_args()

    meta = {}
    if (EPIS / "_smoke_meta.json").exists():
        try:
            meta = json.loads((EPIS / "_smoke_meta.json").read_text(encoding="utf-8"))
        except Exception:
            pass
    slug = a.slug or meta.get("slug")
    if not slug:
        raise SystemExit("XX passe --slug (ou gere _smoke_meta.json)")
    ep = Path(meta.get("pasta")) if (meta.get("slug") == slug and meta.get("pasta")) else EPIS / slug
    reg = ep / "automation"
    reg.mkdir(parents=True, exist_ok=True)

    cmd = [PY, str(APP / "render_supervisor.py"), "--slug", slug,
           "--max-restarts", str(a.max_restarts), "--stale-min", str(a.stale_min)]
    if a.attach_pid:
        cmd += ["--attach-pid", str(a.attach_pid)]
    if a.since:
        cmd += ["--since", a.since]

    log = open(reg / "supervisor_stdout.log", "a", encoding="utf-8", buffering=1)
    p = subprocess.Popen(cmd, cwd=str(APP), stdout=log, stderr=subprocess.STDOUT,
                         creationflags=CFG, close_fds=False)
    (reg / "supervisor.pid").write_text(str(p.pid), encoding="utf-8")
    (reg / "supervisor_launch.json").write_text(json.dumps({
        "pid": p.pid, "slug": slug, "cmd": cmd,
        "inicio": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("supervisor destacado iniciado: PID %d | slug=%s" % (p.pid, slug))
    print("status: python render_supervisor.py --status")
    print("logs:   %s" % (reg / "supervisor.log"))


if __name__ == "__main__":
    main()
