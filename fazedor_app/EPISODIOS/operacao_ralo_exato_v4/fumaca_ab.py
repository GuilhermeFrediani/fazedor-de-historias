# -*- coding: utf-8 -*-
"""A/B-1 render — pernas (ii) image_start e (iii) ponte start+end. Controle (i) ja existe."""
import os, sys, glob, time, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
OUTDIR = r"C:\pinokio\api\wan2gp-amd\app\outputs"
EP = r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4"

PERNAS = [
    ("operacao_ralo_exato_v4_c02_ab_start",  "V4AB_START"),
    ("operacao_ralo_exato_v4_c02_ab_bridge", "V4AB_BRIDGE"),
]

for slug, tag in PERNAS:
    st = os.path.join(EP, "settings", slug + "_settings.json")
    print("\n=== [%s] rendendo %s …" % (tag, slug), flush=True)
    t0 = time.time()
    r = subprocess.run([PY, GEN, "--settings", st, "--tag", tag], cwd=CWD)
    dur = (time.time() - t0) / 60.0
    mp4 = None
    for f in glob.glob(os.path.join(OUTDIR, slug + "*.mp4")):
        mp4 = f
    if r.returncode == 0 and mp4:
        print("=== [%s] OK em %.1f min → %s" % (tag, dur, os.path.basename(mp4)), flush=True)
    else:
        print("=== [%s] FALHOU rc=%d após %.1f min" % (tag, r.returncode, dur), flush=True)
        sys.exit(1)
print("\n>>> A/B-1 RENDERIZADO (ii e iii) — julgamento com o gate + olhos humanos")
