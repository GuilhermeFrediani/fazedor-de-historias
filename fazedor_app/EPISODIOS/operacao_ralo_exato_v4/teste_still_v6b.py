# -*- coding: utf-8 -*-
"""TESTE B retry — guia estatico com fallback de duracao.

O primeiro teste B abortou no watchdog (VRAM reservada 16016 > 15872 em 1
amostra, 144 MB acima do limite). Estrategia: retry 10s; se abortar de novo,
degrada para 5s (metade da memoria de latentes) que valida o mesmo conceito
(estabilidade de set com guia estatico). Gate + PSNR + frames na saida.
"""
import json, re, subprocess, sys, time
from pathlib import Path
import os

# Anti-fragmentacao do pool de VRAM: os aborts mostraram alocado 8654 MB com
# RESERVADO 16016-16760 MB (7,4 GB presos em blocos fragmentados durante o
# encoding_text). max_split_size_mb reduz a sobre-reserva do alocador.
# Herdado pelo gen_test via ambiente (lido antes do import do torch la dentro).
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao
KEY = qc_visao._chave()

ANCORA = EP / "refs" / "ancora_calada.png"
ST_C06 = EP / "settings" / "operacao_ralo_exato_v4_c06_climax_settings.json"
STILL = EP / "refs" / "v6_still_guide.mp4"
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")
PROPS = ("white wall telephone box with handset and coiled cord, fallen steel grate, steel "
         "drum, rubber test plug, absorbent pads / swollen pillow, white paper sack, bucket "
         "cart with plastic buckets, squeegee, floor-wash pedal, pressure hose reel, "
         "red-wheel water valves, wall-mounted pressure gauges, steel pipes along the walls, "
         "chain with hook, white canvas curtain, broom, tape measure, carpenter pencil, "
         "caged industrial lamps, wet concrete floor with yellow safety lines, folded metal "
         "ruler, military client in olive uniform ONLY when announced by the estado")


def psnr_png(a, b):
    r = subprocess.run([FF, "-hide_banner", "-i", str(a), "-i", str(b),
                        "-filter_complex", "psnr", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"average:([0-9.]+|inf)", r.stderr)
    return (float(m.group(1)) if m.group(1) != "inf" else 99.0) if m else None


def extrair(mp4, ts, png):
    subprocess.run([FF, "-y", "-ss", str(ts), "-i", str(mp4), "-frames:v", "1", str(png)],
                   capture_output=True)


st = json.loads(ST_C06.read_text(encoding="utf-8"))
mo_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", st["prompt"])
estado_end = mo_end.group(1) if mo_end else ""

base = {k: st[k] for k in ("num_inference_steps", "resolution", "force_fps", "guidance_scale",
                           "flow_shift", "skip_steps_cache_type", "audio_prompt_type",
                           "activated_loras", "loras_multipliers", "config", "_cli_extra")}

resultado = None
for vl, sufixo, seed in (("10s", "still", 8001), ("5s", "still5", 8001)):
    overlay = dict(base)
    overlay.update({
        "model_type": "minimax_h3_control_pruned",
        "output_filename": "v6_c06_" + sufixo,
        "seed": seed,
        "video_length": vl,
        "video_guide": str(STILL),
        "video_prompt_type": "SV",
        "control_net_weight": 0.4,
        "image_start": str(ANCORA),
        "image_prompt_type": "S",
        "prompt": st["prompt"] + ALINHA,
    })
    sdf = EP / "settings" / ("v6_c06_" + sufixo + "_settings.json")
    sdf.write_text(json.dumps(overlay, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== v6_c06_%s (%s, weight 0.4, seed %d) ===" % (sufixo, vl, seed), flush=True)
    t0 = time.time()
    r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", "V6_" + sufixo.upper()],
                       cwd=CWD)
    print("  rc=%d · %.1f min" % (r.returncode, (time.time() - t0) / 60), flush=True)
    mp4s = list(OUT.glob("v6_c06_%s*.mp4" % sufixo))
    if r.returncode == 0 and mp4s:
        resultado = (vl, sufixo, mp4s[0])
        break
    print("  (abort/falha — %s)" % ("degradando para 5s" if vl == "10s" else "fim"), flush=True)

if not resultado:
    print("XX ambos falharam", flush=True)
    sys.exit(2)

vl, sufixo, mp4 = resultado
rel = {"guia": str(STILL), "video_length": vl, "mp4": str(mp4)}
print("\n=== PROVA (%s) ===" % vl, flush=True)
ult = "9.9" if vl == "10s" else "4.9"
meio = "7.5" if vl == "10s" else "3.5"
for ts in ("0.2", "1.2", meio, "6.0", ult):
    if float(ts) < float(vl.rstrip("s")):
        extrair(mp4, ts, EP / "refs" / ("v6" + sufixo + "_f" + ts.replace(".", "") + ".png"))
ps = psnr_png(EP / "refs" / ("v6" + sufixo + "_f02.png"), ANCORA)
print("  f0.2 vs ancora = %.1f dB" % (ps if ps is not None else -1), flush=True)
j = qc_visao.gate_ancora(KEY, str(EP / "refs" / ("v6" + sufixo + "_f" + ult.replace(".", "") + ".png")),
                         estado=estado_end, props=PROPS)
print("  GATE f%s: %s — %s" % (ult, j.get("veredito"), j.get("motivo", "")), flush=True)
print("  cenario_violado:", j.get("cenario_violado"), flush=True)
rel["psnr_f0"] = ps
rel["gate"] = j
(EP / "v6_still_relatorio.json").write_text(
    json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n>>> TESTE B (retry %s) completo — relatorio: v6_still_relatorio.json" % vl, flush=True)
