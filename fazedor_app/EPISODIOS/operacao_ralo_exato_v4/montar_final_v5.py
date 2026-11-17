# -*- coding: utf-8 -*-
"""Monta o FINAL v5 do teste 60 s: os 6 clipes APROVADOS pelo gate ->
pos-producao (loudnorm -14 LUFS + punch-in + faststart) -> gate episodico."""
import json, shutil, subprocess, sys, re, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao
KEY = qc_visao._chave()
FINAL_DIR = EP / "final"
FINAL_DIR.mkdir(exist_ok=True)

# 1) achar o c01 cujo ultimo frame = ancora_limpa_t3.png (o render aprovado)
ref = EP / "refs" / "ancora_limpa_t3.png"
cands = sorted(glob.glob(str(OUT / "operacao_ralo_exato_v4_c01_ligacao*.mp4")),
               key=lambda p: Path(p).stat().st_mtime, reverse=True)
c01 = None
for cand in cands:
    tmp = FINAL_DIR / "_probe.png"
    subprocess.run([FF, "-y", "-ss", "9.9", "-i", cand, "-frames:v", "1", str(tmp)], capture_output=True)
    ps = subprocess.run([FF, "-i", str(tmp), "-i", str(ref), "-lavfi", "psnr", "-f", "null", "-"],
                        capture_output=True, text=True)
    m = re.search(r"average:([\d.]+)", ps.stderr)
    db = float(m.group(1)) if m else 0
    print("c01 candidato: %s · PSNR %.1f dB" % (Path(cand).name, db))
    if db >= 30:
        c01 = cand
        break
if not c01:
    print("XX nenhum c01 casa com a ancora aprovada — usar o mais recente por conta e risco")
    c01 = cands[0]
print("c01 aprovado escolhido: %s" % Path(c01).name)

# 2) os 6 aprovados, em ordem, para a pasta final
aprovados = [
    ("c01", c01),
    ("c02", OUT / "operacao_ralo_exato_v4_c02_cadeia.mp4"),
    ("c03", OUT / "operacao_ralo_exato_v4_c03_primeira_falha_v2.mp4"),
    ("c04", OUT / "operacao_ralo_exato_v4_c04_jeitinho.mp4"),
    ("c05", OUT / "operacao_ralo_exato_v4_c05_escalada.mp4"),
    ("c06", OUT / "operacao_ralo_exato_v4_c06_climax_v2.mp4"),
]
for f in FINAL_DIR.glob("*.mp4"):
    f.unlink()
for nome, src in aprovados:
    dst = FINAL_DIR / (nome + "_" + Path(src).name)
    shutil.copy2(src, dst)
    print("stage: %s (%.1f MB)" % (dst.name, dst.stat().st_size / 1048576))

# 3) pos-producao
r = subprocess.run([PY, str(PIPE / "pos_producao.py"), "--pasta", str(FINAL_DIR),
                    "--padrao", "*.mp4",
                    "--saida", str(EP / "operacao_ralo_exato_v4_v5_FINAL.mp4")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-700:])

# 4) gate episodico no FINAL
r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--settings", str(EP / "settings"),
                    "--saida", str(EP / "qc_final_v5.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-900:])
final = EP / "operacao_ralo_exato_v4_v5_FINAL.mp4"
if final.exists():
    print("\n>>> FINAL v5:", final, "(%.1f MB)" % (final.stat().st_size / 1048576))
