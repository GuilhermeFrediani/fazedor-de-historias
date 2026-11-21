# -*- coding: utf-8 -*-
"""Fecha a ponte do clipe 2 com o ESTADO_OUT PINADO:
ancora limpa (seed 7003) -> draft 5s do delta -> keyframe de saida (gate) ->
ponte 10 s (image_start + image_end) -> gate das pontas -> ancora para o clipe 3."""
import json, subprocess, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
from gerar_keyframe_saida import gerar_keyframe

ANCORA = EP / "refs" / "ancora_limpa_t3.png"
SLUG = "operacao_ralo_exato_v4_c02_ponte"
TAG = "PONTE_C02"
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced, and by the end of the target video the "
          "scene matches <Picture 2>.")

st1 = json.loads((SETDIR / "operacao_ralo_exato_v4_c01_ligacao_settings.json").read_text(encoding="utf-8"))
st2 = json.loads((SETDIR / "operacao_ralo_exato_v4_c02_chegada_settings.json").read_text(encoding="utf-8"))
estado_in = re.search(r"AT START: (.+?)\. \[Shot", st2["prompt"]).group(1)
estado_out = re.search(r"AT END: (.+?)\.?(?:\n|$)", st2["prompt"]).group(1)
print("estado_in : %s" % estado_in)
print("estado_out: %s" % estado_out, flush=True)

# 1) keyframe de saida (draft 5s do delta + gate)
kf, veredito = gerar_keyframe(ANCORA, estado_in, estado_out, str(SETDIR / "operacao_ralo_exato_v4_c02_chegada_settings.json"),
                              "operacao_ralo_exato_v4_c02_saida")
if not kf:
    print("XX keyframe de saida REPROVADO — a ponte nao prossegue sem as duas pontas sadias.", flush=True)
    sys.exit(3)
print("KEYFRAME DE SAIDA APROVADO: %s" % kf, flush=True)

# 2) ponte completa (start + end) com o prompt integral v4.1
st = dict(st2)
st["output_filename"] = SLUG
st["image_start"] = str(ANCORA)
st["image_end"] = kf
st["image_prompt_type"] = "SE"
st["prompt"] = st2["prompt"] + ALINHA
(SETDIR / (SLUG + "_settings.json")).write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
print("\n=== PONTE 10 s (start+end) ===", flush=True)
import time
t0 = time.time()
r = subprocess.run([PY, r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py",
                    "--settings", str(SETDIR / (SLUG + "_settings.json")), "--tag", TAG],
                   cwd=r"C:\Users\Guilherme\Documents\Projeto Padrão")
mp4s = list(OUT.glob(SLUG + "*.mp4"))
print("render rc=%d · %.1f min · %s" % (r.returncode, (time.time() - t0) / 60,
      mp4s[0].name if mp4s else "SEM MP4"), flush=True)
if r.returncode != 0 or not mp4s:
    sys.exit(1)
mp4 = mp4s[0]

# 3) gate das pontas do clipe 2
r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(OUT),
                    "--padrao", SLUG + "_*.mp4", "--settings", str(SETDIR),
                    "--saida", str(EP / "qc_ponte_c02.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-800:], flush=True)

# 4) ancora do clipe 2 para o clipe 3
sys.path.insert(0, str(PIPE))
import qc_visao
KEY = qc_visao._chave()
f9 = EP / "refs" / "ancora_c02_ponte.png"
subprocess.run([FF, "-y", "-ss", "9.9", "-i", str(mp4), "-frames:v", "1", str(f9)], capture_output=True)
j2 = qc_visao.gate_ancora(KEY, str(f9), estado_out)
print("[ANCORA c02 p/ clipe 3] %s — %s" % (j2.get("veredito"), j2.get("motivo", "")), flush=True)
(EP / "ponte_c02_relatorio.json").write_text(json.dumps({
    "ancora_in": str(ANCORA), "keyframe_out": kf, "keyframe_veredito": veredito,
    "mp4": str(mp4), "gate_ancora_c02": j2,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n>>> PONTE DO CLIPE 2 CONCLUIDA — relatorio: ponte_c02_relatorio.json", flush=True)
