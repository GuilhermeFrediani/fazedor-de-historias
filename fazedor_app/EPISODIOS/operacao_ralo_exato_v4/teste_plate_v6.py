# -*- coding: utf-8 -*-
"""TESTE V6 — ControlNet-Union "set-plate" (validacao de 1 clipe antes do episodio).

Arquitetura: ancora -> PLATE -> clipe controlado.
  PLATE  = render fl2va normal de 10s a partir da ancora (bonecos parados, camera
           travada) — e a "placa de set" com teto/paredes/piso congelados.
  CLIPE  = minimax_h3_control_pruned com video_guide=plate (SV, weight 0.4) +
           image_start=ancora (handler exige que casem — casam por construcao).
Comparacao direta contra o c06 do v5 (mesmo prompt, mesma ancora, SEM controle)
que apresentou o pior drift (teto vira ceu 51-56s).
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

ANCORA = EP / "refs" / "ancora_calada.png"          # ancora APROVADA do c05
ST_C06 = EP / "settings" / "operacao_ralo_exato_v4_c06_climax_settings.json"
C06_V5 = OUT / "operacao_ralo_exato_v4_c06_climax_v2.mp4"  # o c06 do v5 (com drift)
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
    """PSNR entre 2 PNGs (dB) ou None se falhar."""
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


def rodar(overlay, tag):
    sdf = EP / "settings" / (overlay["output_filename"] + "_settings.json")
    sdf.write_text(json.dumps(overlay, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== %s ===" % overlay["output_filename"], flush=True)
    t0 = time.time()
    r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", tag], cwd=CWD)
    print("  rc=%d · %.1f min" % (r.returncode, (time.time() - t0) / 60), flush=True)
    mp4s = list(OUT.glob(overlay["output_filename"] + "*.mp4"))
    return (r.returncode, mp4s[0] if mp4s else None)


st = json.loads(ST_C06.read_text(encoding="utf-8"))
prompt_c06 = st["prompt"]
mo_start = re.search(r"AT START: (.+?)\. \[Shot", prompt_c06, flags=16)
estado_start = mo_start.group(1).replace("\\", "")
mo_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", prompt_c06)
estado_end = mo_end.group(1) if mo_end else ""
set_par = prompt_c06.split("AT START:")[0]  # paragrafo de set verbatim

base = {k: st[k] for k in ("num_inference_steps", "resolution", "force_fps", "guidance_scale",
                           "flow_shift", "skip_steps_cache_type", "audio_prompt_type",
                           "activated_loras", "loras_multipliers", "config", "_cli_extra")}

rel = {"ancora": str(ANCORA)}

# ---------------------------------------------------------------- 1) PLATE
plate_prompt = (set_par + "AT START: " + estado_start + ". "
                "[Shot 1] Locked-off wide shot of the same bay: TEO stands exactly where he "
                "is on the white sack and JUCA stands exactly where he is holding the chain "
                "and hook; both puppets only breathe with subtle idle motion, tiny weight "
                "shifts, blinking. Nothing falls, nothing moves, no new object enters, the "
                "ceiling, walls, floor and every prop stay perfectly still. "
                "[Shot 2] At 00:05.000, the camera keeps the exact same wide locked shot; "
                "the scene holds perfectly still, only the subtle idle breathing continues. "
                "For the target video, at 0.00 seconds into the target video, <Picture 1> "
                "(from [Shot 1]) is fully referenced.")
plate = dict(base)
plate.update({
    "model_type": "minimax_h3_fl2va_pruned",
    "output_filename": "v6_plate_c06",
    "seed": 8100,
    "video_length": "10s",
    "image_start": str(ANCORA),
    "image_prompt_type": "S",
    "prompt": plate_prompt,
})
rc, mp4_plate = rodar(plate, "V6_PLATE")
if rc != 0 or not mp4_plate:
    print("XX plate falhou — teste abortado", flush=True)
    sys.exit(2)
extrair(mp4_plate, 0.2, EP / "refs" / "v6_plate_f0.png")
extrair(mp4_plate, 5.0, EP / "refs" / "v6_plate_f5.png")
extrair(mp4_plate, 9.9, EP / "refs" / "v6_plate_f9.png")
ps_plate = psnr_png(EP / "refs" / "v6_plate_f0.png", ANCORA)
print("  plate: f0.2 vs ancora = %.1f dB" % (ps_plate if ps_plate is not None else -1), flush=True)
rel["plate"] = {"mp4": str(mp4_plate), "psnr_f0_vs_ancora": ps_plate}

# ------------------------------------------------------- 2) CLIPE CONTROLADO
ctrl = dict(base)
ctrl.update({
    "model_type": "minimax_h3_control_pruned",
    "output_filename": "v6_c06_ctrl",
    "seed": 8001,
    "video_length": "10s",
    "video_guide": str(mp4_plate),
    "video_prompt_type": "SV",
    "control_net_weight": 0.4,
    "image_start": str(ANCORA),
    "image_prompt_type": "S",
    "prompt": prompt_c06 + ALINHA,
})
rc, mp4_ctrl = rodar(ctrl, "V6_CTRL")
if rc != 0 or not mp4_ctrl:
    print("XX clipe controlado falhou — teste abortado", flush=True)
    sys.exit(3)
rel["ctrl"] = {"mp4": str(mp4_ctrl)}

# ------------------------------------------------------------------ 3) PROVA
print("\n=== PROVA: frames do clipe controlado ===", flush=True)
for ts in ("0.2", "2.5", "5.0", "7.5", "9.9"):
    extrair(mp4_ctrl, ts, EP / "refs" / ("v6_ctrl_f" + ts.replace(".", "") + ".png"))
ps_ctrl = psnr_png(EP / "refs" / "v6_ctrl_f02.png", ANCORA)
print("  ctrl: f0.2 vs ancora = %.1f dB (encadeamento segurou?)" % (ps_ctrl if ps_ctrl else -1),
      flush=True)
j = qc_visao.gate_ancora(KEY, str(EP / "refs" / "v6_ctrl_f99.png"),
                         estado=estado_end, props=PROPS)
print("  GATE ANCORA ctrl (f9.9): %s — %s" % (j.get("veredito"), j.get("motivo", "")), flush=True)
print("  objetos nao plantados:", j.get("objetos_nao_plantados"), flush=True)
rel["ctrl"]["psnr_f0_vs_ancora"] = ps_ctrl
rel["ctrl"]["gate_f99"] = j

# comparacao com o c06 do v5 (mesmo prompt, sem controle)
if C06_V5.exists():
    extrair(C06_V5, 5.0, EP / "refs" / "v5_c06_f5.png")
    extrair(C06_V5, 7.5, EP / "refs" / "v5_c06_f75.png")
    print("  (frames do v5 c06 extraidos para comparacao visual)", flush=True)

(EP / "v6_plate_relatorio.json").write_text(
    json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n>>> TESTE V6 completo — relatorio: v6_plate_relatorio.json", flush=True)
print(">>> conferir olhos nus: refs/v6_ctrl_f25/f50/f75 vs refs/v5_c06_f5/f75 "
      "(o teto sobrevive?)", flush=True)
