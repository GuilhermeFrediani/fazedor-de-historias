# -*- coding: utf-8 -*-
"""montar_final_v8.py — FINAL 60 s no modo 2 steps / 832x480.

- c01/c02: 20 s JA APROVADO (8/640) -> reduz para 832x480 (lanczos) na montagem
- c03..c06: clipes nativos 832x480 da cadeia v8
- pos_producao (--cortar-meio) + gate episodico
Saida: operacao_ralo_exato_v4_v8_FINAL60s.mp4 + qc_final_v8.json
Nao toca em final_v7, no 20 s parcial nem nos arquivos v7.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
PIPE = EP.parent.parent.parent / "pipeline"
SETDIR = EP / "settings"
FINAL_DIR = EP / "final_v8"
SAIDA = EP / "operacao_ralo_exato_v4_v8_FINAL60s.mp4"
ORDEM = ["c01", "c02", "c03", "c04", "c05", "c06"]
RES = "832:480"

rel = json.loads((EP / "cadeia_v8_relatorio.json").read_text(encoding="utf-8"))
clips = {}
for f in rel:
    if f.get("mp4") and f.get("aprovado"):
        clips[f["curto"]] = f["mp4"]
    elif f.get("curto"):
        print("!! %s NAO aprovado (fallback/parada) — montagem cancelada" % f["curto"])
faltam = [c for c in ORDEM if c not in clips]
if faltam:
    print("XX cadeia v8 incompleta: faltam %s — emenda cancelada." % faltam)
    sys.exit(2)
print("clipes v8:")
for c in ORDEM:
    print("  %s = %s" % (c, Path(clips[c]).name))

# limpa apenas a pasta desta montagem
FINAL_DIR.mkdir(exist_ok=True)
for f in FINAL_DIR.glob("*.mp4"):
    f.unlink()


def alias_settings(stem):
    """Garante <stem>_settings.json para o QC episodico achar AT START/AT END."""
    exato = SETDIR / (stem + "_settings.json")
    if exato.exists():
        return exato.name
    base = re.sub(r"\(\d+\)$", "", stem)
    cand = SETDIR / (base + "_settings.json")
    if cand.exists():
        exato.write_text(cand.read_text(encoding="utf-8"), encoding="utf-8")
        return "%s <- %s" % (exato.name, cand.name)
    # ultimo recurso: settings cujo nome e prefixo do stem (mais longo)
    pref = sorted((p for p in SETDIR.glob("*_settings.json") if stem.startswith(p.stem[:-9])),
                  key=lambda p: len(p.stem), reverse=True)
    if pref:
        exato.write_text(pref[0].read_text(encoding="utf-8"), encoding="utf-8")
        return "%s <- %s" % (exato.name, pref[0].name)
    return "SEM SETTINGS"


for c in ORDEM:
    src = Path(clips[c])
    stem = src.stem
    dst = FINAL_DIR / (stem + ".mp4")
    if c in ("c01", "c02"):
        r = subprocess.run([FF, "-y", "-i", str(src), "-vf",
                            "scale=%s:flags=lanczos" % RES,
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                            "-pix_fmt", "yuv420p", "-c:a", "copy", str(dst)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("stage %s: 640->480 %s (%.1f MB)" % (c, "ok" if dst.exists() else r.stderr[-300:],
                                                   dst.stat().st_size / 1048576 if dst.exists() else 0))
    else:
        shutil.copy2(src, dst)
        print("stage %s: copia nativa %s (%.1f MB)" % (c, dst.name, dst.stat().st_size / 1048576))
    print("  settings:", alias_settings(stem))

print("\n>>> pos_producao (--cortar-meio)...")
r = subprocess.run([PY, str(PIPE / "pos_producao.py"), "--pasta", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--cortar-meio", "--saida", str(SAIDA)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-900:])

print("\n>>> gate episodico...")
r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--settings", str(SETDIR),
                    "--saida", str(EP / "qc_final_v8.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-1400:])

if SAIDA.exists():
    d = subprocess.run([FF, "-i", str(SAIDA)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", d.stderr)
    print("\n>>> FINAL v8:", SAIDA, "| dur:", m.group(1) if m else "?",
          "| %.1f MB" % (SAIDA.stat().st_size / 1048576))
else:
    print("XX pos-producao nao gerou o arquivo final")
    sys.exit(3)
