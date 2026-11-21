# -*- coding: utf-8 -*-
"""Monta o FINAL v7: os 6 clipes NOVOS da cadeia v7 (c01..c06) -> pos-producao
com --cortar-meio -> gate episodico. Nao toca no v5_FINAL nem no v6a_PATCH —
tudo em final_v7/ e _v7_FINAL.mp4.
"""
import json, subprocess, sys, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
PIPE = EP.parent.parent.parent / "pipeline"
FINAL_DIR = EP / "final_v7"
FINAL_DIR.mkdir(exist_ok=True)
SAIDA = EP / "operacao_ralo_exato_v4_v7_FINAL.mp4"
ORDEM = ["c01", "c02", "c03", "c04", "c05", "c06"]

rel = json.loads((EP / "cadeia_v7_relatorio.json").read_text(encoding="utf-8"))
clips = {}
for f in rel:
    if f.get("mp4") and (f.get("aprovado") or f.get("fallback")):
        clips[f["curto"]] = f["mp4"]
        if f.get("fallback"):
            print("!! %s entra como FALLBACK (gate nao aprovou) — sujeito a nova rodada"
                  % f["curto"])
faltam = [c for c in ORDEM if c not in clips]
if faltam:
    print("XX cadeia v7 incompleta: faltam %s — emenda cancelada." % faltam)
    sys.exit(2)
print("clipes v7: " + ", ".join("%s=%s" % (c, Path(clips[c]).name) for c in ORDEM))

for f in FINAL_DIR.glob("*.mp4"):
    f.unlink()
for c in ORDEM:
    src = Path(clips[c])
    dst = FINAL_DIR / (c + "_" + src.name)
    shutil.copy2(src, dst)
    print("stage: %s (%.1f MB)" % (dst.name, dst.stat().st_size / 1048576))

r = subprocess.run([PY, str(PIPE / "pos_producao.py"), "--pasta", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--cortar-meio", "--saida", str(SAIDA)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-700:])

r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--settings", str(EP / "settings"),
                    "--saida", str(EP / "qc_final_v7.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-1200:])
if SAIDA.exists():
    print("\n>>> FINAL v7:", SAIDA, "(%.1f MB)" % (SAIDA.stat().st_size / 1048576))
else:
    print("XX pos-producao nao gerou o arquivo final")
    sys.exit(3)
