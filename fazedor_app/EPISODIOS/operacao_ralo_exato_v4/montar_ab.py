# -*- coding: utf-8 -*-
"""A/B-1 — encadeamento visual no clipe 2 (mesmo seed 7001):
  (i)  controle   = ja existe (operacao_ralo_exato_v4_c02_chegada.mp4, texto puro)
  (ii) ab_start   = image_start = ultimo frame do clipe 1
  (iii)ab_bridge  = image_start + image_end (ponte FL2VA entre dois estados)
As refs nascem dos frames reais ja renderizados. Saida: settings\\*ab_*.json"""
import json, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"
REFS = EP / "refs"
REFS.mkdir(exist_ok=True)

# 1) frames de referencia dos renders reais
refs = {}
for nome, fonte, t in [("ref_start_c01_fim", "operacao_ralo_exato_v4_c01_ligacao.mp4", "9.9"),
                       ("ref_end_c02_fim", "operacao_ralo_exato_v4_c02_chegada.mp4", "9.9")]:
    src = OUT / fonte
    dst = REFS / (nome + ".png")
    r = subprocess.run([FF, "-y", "-ss", t, "-i", str(src), "-frames:v", "1", str(dst)], capture_output=True)
    refs[nome] = str(dst)
    print("%s <- %s (rc=%d)" % (dst.name, fonte, r.returncode))

# 2) base = settings atuais do clipe 2 (v4.1: com AT START/AT END/ocupacao/N-A)
base = json.loads((SETDIR / "operacao_ralo_exato_v4_c02_chegada_settings.json").read_text(encoding="utf-8"))
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")
ALINHA2 = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
           "(from [Shot 1]) is fully referenced, and by the end of the target video the "
           "scene matches <Picture 2>.")

# perna ii — image_start
ii = dict(base)
ii["output_filename"] = "operacao_ralo_exato_v4_c02_ab_start"
ii["image_start"] = refs["ref_start_c01_fim"]
ii["image_prompt_type"] = "S"
ii["prompt"] = base["prompt"] + ALINHA
(SETDIR / (ii["output_filename"] + "_settings.json")).write_text(
    json.dumps(ii, indent=2, ensure_ascii=False), encoding="utf-8")
print("perna ii escrita: %s (prompt %d chars)" % (ii["output_filename"], len(ii["prompt"])))

# perna iii — ponte start + end
iii = dict(base)
iii["output_filename"] = "operacao_ralo_exato_v4_c02_ab_bridge"
iii["image_start"] = refs["ref_start_c01_fim"]
iii["image_end"] = refs["ref_end_c02_fim"]
iii["image_prompt_type"] = "SE"
iii["prompt"] = base["prompt"] + ALINHA2
(SETDIR / (iii["output_filename"] + "_settings.json")).write_text(
    json.dumps(iii, indent=2, ensure_ascii=False), encoding="utf-8")
print("perna iii escrita: %s (prompt %d chars)" % (iii["output_filename"], len(iii["prompt"])))
print("A/B pronto: controle (i) ja renderizado · ii e iii aguardando GPU")
