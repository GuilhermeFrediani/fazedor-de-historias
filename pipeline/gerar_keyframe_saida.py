# -*- coding: utf-8 -*-
"""
gerar_keyframe_saida.py — o EDIT de keyframe da ponte (a peça que faltava).
Dado: ancora aprovada (frame de inicio) + estado_out prometido (EN).
Faz: render DRAFT de 5 s (image_start = ancora, prompt so do delta) ->
     ultimo frame = candidato a image_end -> GATE de visao com o estado_out.
Devolve (caminho do keyframe, verdicto) — se APROVADA, o keyframe pode pinar o fim.

Uso (como modulo):
    from gerar_keyframe_saida import gerar_keyframe
    png, veredito = gerar_keyframe(ancora_png, estado_in, estado_out, base_settings, slug)
"""
import json, subprocess, sys, time, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
import qc_visao
KEY = qc_visao._chave()


def _head_do_prompt(prompt_base):
    """Cabecalho de identidade do prompt v4.1: ate o 'AT START:'."""
    i = prompt_base.find("AT START:")
    return prompt_base[:i].strip() if i > 0 else prompt_base[:800]


def gerar_keyframe(ancora_png, estado_in, estado_out, base_settings, slug, tentativas=2):
    """Render draft 5 s do delta -> ultimo frame -> gate. Retorna (png|None, veredito_str)."""
    base = json.loads(Path(base_settings).read_text(encoding="utf-8"))
    head = _head_do_prompt(base.get("prompt", ""))
    for tent in range(tentativas):
        st = dict(base)
        st["output_filename"] = slug + ("_t%d" % (tent + 1) if tent else "")
        st["video_length"] = "5s"
        st["seed"] = int(base.get("seed", 7001)) + tent
        st["image_start"] = str(ancora_png)
        st["image_prompt_type"] = "S"
        st["prompt"] = (head + " AT START: " + estado_in.rstrip(".") + ". AT END: " +
                        estado_out.rstrip(".") + ". The camera holds one continuous static wide "
                        "shot and the scene settles exactly on the end state. They do not speak "
                        "and their mouths do not move."
                        " For the target video, at 0.00 seconds into the target video, <Picture 1> "
                        "(from [Shot 1]) is fully referenced."
                        + "\noverall_soundscape: " + str(base.get("overall_soundscape", "")).strip()
                        + "\nnon_diegetic_music: N/A")
        st["prompt"] = " ".join(st["prompt"].split("\nintegrated")[:1]) if False else st["prompt"]
        sdf = AQUI.parent / "fazedor_app" / "EPISODIOS" / "_keyframes"
        sdf.mkdir(exist_ok=True)
        arq = sdf / (st["output_filename"] + "_settings.json")
        arq.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print("  draft 5s: %s (seed %d)" % (st["output_filename"], st["seed"]), flush=True)
        t0 = time.time()
        r = subprocess.run([PY, GEN, "--settings", str(arq), "--tag", "KF_" + slug[-12:]], cwd=CWD)
        mp4s = list(OUT.glob(st["output_filename"] + "*.mp4"))
        if r.returncode != 0 or not mp4s:
            print("  draft falhou rc=%d" % r.returncode, flush=True)
            continue
        mp4 = mp4s[0]
        print("  draft ok em %.1f min" % ((time.time() - t0) / 60), flush=True)
        # candidato = ultimo frame do draft
        cand = Path(ancora_png).parent / (slug + "_keyframe.png")
        subprocess.run([FF, "-y", "-ss", "4.4", "-i", str(mp4), "-frames:v", "1", str(cand)],
                       capture_output=True)
        if not cand.exists():
            continue
        j = qc_visao.gate_ancora(KEY, str(cand), estado_out)
        print("  GATE keyframe: %s — %s" % (j.get("veredito"), j.get("motivo", "")), flush=True)
        print("  extras=%s flutuantes=%s" % (j.get("personagens_extras"), j.get("objetos_flutuantes")), flush=True)
        if j.get("veredito") == "APROVADA":
            return str(cand), "APROVADA"
    return None, "REPROVADA (%d tentativas)" % tentativas
