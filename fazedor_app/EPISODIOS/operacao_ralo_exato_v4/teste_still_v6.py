# -*- coding: utf-8 -*-
"""TESTE B — video-guia ESTATICO (drift zero por construcao).

Licao do teste A: o plate renderizado de 10s "idle" deriva (derrubou o tambor,
alargou o ceu) e o ControlNet transmite a deriva fielmente. O guia certo e um
video ESTÁTICO feito do PNG da ancora via ffmpeg (0 GPU, pixel congelado):
o SV soft-shapes dele = esqueleto do set congelado; o prompt anima a acao.
Comparacao contra o teste A (plate movel) e o v5 (sem controle).
"""
import json, re, subprocess, sys, time
from pathlib import Path

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
    if not m:
        return None
    return float(m.group(1)) if m.group(1) != "inf" else 99.0


def extrair(mp4, ts, png):
    subprocess.run([FF, "-y", "-ss", str(ts), "-i", str(mp4), "-frames:v", "1", str(png)],
                   capture_output=True)


st = json.loads(ST_C06.read_text(encoding="utf-8"))
mo_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", st["prompt"])
estado_end = mo_end.group(1) if mo_end else ""

# ------------------------------------------------------- 1) guia estatico (0 GPU)
if not STILL.exists():
    subprocess.run([FF, "-y", "-loop", "1", "-framerate", "24", "-i", str(ANCORA),
                    "-frames:v", "243", "-c:v", "libx264", "-preset", "fast",
                    "-pix_fmt", "yuv420p", str(STILL)], capture_output=True)
print("guia estatico: %s (%.1f KB)" % (STILL.name,
      STILL.stat().st_size / 1024 if STILL.exists() else -1), flush=True)

# ------------------------------------------------------- 2) render controlado
overlay = {k: st[k] for k in ("num_inference_steps", "resolution", "force_fps",
                              "guidance_scale", "flow_shift", "skip_steps_cache_type",
                              "audio_prompt_type", "activated_loras", "loras_multipliers",
                              "config", "_cli_extra")}
overlay.update({
    "model_type": "minimax_h3_control_pruned",
    "output_filename": "v6_c06_still",
    "seed": 8001,
    "video_length": "10s",
    "video_guide": str(STILL),
    "video_prompt_type": "SV",
    "control_net_weight": 0.4,
    "image_start": str(ANCORA),
    "image_prompt_type": "S",
    "prompt": st["prompt"] + ALINHA,
})
sdf = EP / "settings" / "v6_c06_still_settings.json"
sdf.write_text(json.dumps(overlay, indent=2, ensure_ascii=False), encoding="utf-8")
print("\n=== v6_c06_still (guia estatico, weight 0.4, seed 8001) ===", flush=True)
t0 = time.time()
r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", "V6_STILL"], cwd=CWD)
print("  rc=%d · %.1f min" % (r.returncode, (time.time() - t0) / 60), flush=True)
mp4s = list(OUT.glob("v6_c06_still*.mp4"))
if r.returncode != 0 or not mp4s:
    print("XX render falhou", flush=True)
    sys.exit(2)
mp4 = mp4s[0]

# ------------------------------------------------------------------ 3) prova
rel = {"guia": str(STILL), "mp4": str(mp4)}
print("\n=== PROVA ===", flush=True)
for ts in ("0.2", "2.5", "5.0", "7.5", "9.9"):
    extrair(mp4, ts, EP / "refs" / ("v6still_f" + ts.replace(".", "") + ".png"))
ps = psnr_png(EP / "refs" / "v6still_f02.png", ANCORA)
print("  f0.2 vs ancora = %.1f dB" % (ps if ps is not None else -1), flush=True)
j = qc_visao.gate_ancora(KEY, str(EP / "refs" / "v6still_f99.png"),
                         estado=estado_end, props=PROPS)
print("  GATE f9.9: %s — %s" % (j.get("veredito"), j.get("motivo", "")), flush=True)
print("  cenario_violado:", j.get("cenario_violado"), flush=True)
rel["psnr_f0"] = ps
rel["gate_f99"] = j

# enforcement retroativo: o ceu dos frames do teste A e do plate agora pega?
for nome in ("v6_ctrl_f25", "v6_ctrl_f75", "v6_plate_f9"):
    f = EP / "refs" / (nome + ".png")
    if f.exists():
        ja = qc_visao.gate_ancora(KEY, str(f), props=PROPS)
        print("  retro %s: %s (%s)" % (nome, ja.get("veredito"),
                                       "; ".join(ja.get("cenario_violado", []))), flush=True)

(EP / "v6_still_relatorio.json").write_text(
    json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n>>> TESTE B completo — relatorio: v6_still_relatorio.json", flush=True)
