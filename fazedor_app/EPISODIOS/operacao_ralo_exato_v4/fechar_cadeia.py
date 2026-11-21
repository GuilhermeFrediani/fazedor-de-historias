# -*- coding: utf-8 -*-
"""Fecha o ciclo da cadeia limpa: julga o clipe 2 (ponte da ancora limpa) e
prepara a ancora dele para o clipe 3."""
import json, subprocess, sys
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

mp4_2 = OUT / "operacao_ralo_exato_v4_c02_cadeia.mp4"
assert mp4_2.exists(), "mp4 do clipe 2 nao encontrado"
refs = EP / "refs"
refs.mkdir(exist_ok=True)

# 1) PSNR: primeiro frame do clipe 2 vs a ANCORA LIMPA (seed 7003)
import glob
cand = sorted(glob.glob(str(OUT / "operacao_ralo_exato_v4_c01_ligacao(10).mp4"))) or \
       sorted(glob.glob(str(OUT / "operacao_ralo_exato_v4_c01_ligacao*.mp4")),
              key=lambda p: Path(p).stat().st_mtime)
c01_aprovado = Path(cand[-1])
ancora = refs / "ancora_limpa_t3.png"
subprocess.run([FF, "-y", "-ss", "9.9", "-i", str(c01_aprovado), "-frames:v", "1", str(ancora)], capture_output=True)
f0 = refs / "c02_cadeia_f0.png"
subprocess.run([FF, "-y", "-ss", "0.2", "-i", str(mp4_2), "-frames:v", "1", str(f0)], capture_output=True)
psnr_out = subprocess.run([FF, "-i", str(f0), "-i", str(ancora), "-lavfi", "psnr", "-f", "null", "-"],
                          capture_output=True, text=True)
m = __import__("re").search(r"average:([\d.]+)", psnr_out.stderr)
print("[PONTE] 1o frame do clipe 2 vs ancora limpa (seed 7003): PSNR %s dB" % (m.group(1) if m else "?"))

# 2) GATE de visao do clipe 2 (4 frames vs estado prometido)
r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(OUT),
                    "--padrao", "operacao_ralo_exato_v4_c02_cadeia*.mp4",
                    "--settings", str(EP / "settings"),
                    "--saida", str(EP / "qc_cadeia_c02.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-900:])

# 3) ANCORA do clipe 2 (para o clipe 3) — ultimo frame + gate
f9 = refs / "ancora_c02.png"
subprocess.run([FF, "-y", "-ss", "9.9", "-i", str(mp4_2), "-frames:v", "1", str(f9)], capture_output=True)
st2 = json.loads((EP / "settings" / "operacao_ralo_exato_v4_c02_cadeia_settings.json").read_text(encoding="utf-8"))
import re as _re
mo = _re.search(r"AT END: (.+?)\.?(?:\n|$)", st2["prompt"])
j2 = qc_visao.gate_ancora(KEY, str(f9), mo.group(1) if mo else "")
print("[ANCORA c02] %s — %s" % (j2.get("veredito"), j2.get("motivo", "")))
print("    extras=%s flutuantes=%s" % (j2.get("personagens_extras"), j2.get("objetos_flutuantes")))

(EP / "cadeia_limpa_relatorio.json").write_text(json.dumps({
    "c01_aprovado": {"seed": 7003, "mp4": str(c01_aprovado), "ancora": str(ancora)},
    "c02_ponte": {"mp4": str(mp4_2), "psnr_inicio": m.group(1) if m else "?",
                  "gate": j2, "estado_out": mo.group(1) if mo else "?"},
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n>>> ciclo fechado — relatorio atualizado")
