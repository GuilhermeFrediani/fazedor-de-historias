# -*- coding: utf-8 -*-
"""CADEIA v2 — reality-driven: o pixel manda no estado.
Para cada clipe (3..6): Gemini DESCREVE a ancora real -> essa descricao vira o
AT START do prompt -> render (image_start = ancora, S) -> gate de visao ->
se aprovado, a ancora avanca (ultimo frame real). Reprova: retry seed+1 (1x).
Ao fim: os 4 clipes novos + as 4 ancoras + relatorio."""
import json, subprocess, sys, time, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao
KEY = qc_visao._chave()

ANCORA_INI = EP / "refs" / "ancora_lha_v2.png"   # ancora APROVADA do clipe 3 (seed 7002)
CLIPES = [
    ("operacao_ralo_exato_v4_c04_jeitinho",       "V2_C04"),
    ("operacao_ralo_exato_v4_c05_escalada",       "V2_C05"),
    ("operacao_ralo_exato_v4_c06_climax",         "V2_C06"),
]
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")

# REGISTRO DE PROPS PERMITIDOS (plantados + cenario fixo do set) — v4.3
# licao do teste: lista INCOMPLETA gera falso positivo (painel/gauges ficaram de fora
# e a ancora limpa do c05 quase caiu) — o registro deve cobrir TODO o cenario fixo,
# e deve manter FORA os aderecos proibidos (extintor, rolo de papel, urso...)
PROPS = ("white wall telephone box with handset and coiled cord, fallen steel grate, steel "
         "drum, rubber test plug, absorbent pads / swollen pillow, white paper sack, bucket "
         "cart with plastic buckets, squeegee, floor-wash pedal, pressure hose reel, "
         "red-wheel water valves, wall-mounted pressure gauges, steel pipes along the walls, "
         "chain with hook, white canvas curtain, broom, tape measure, carpenter pencil, "
         "caged industrial lamps, wet concrete floor with yellow safety lines, folded metal "
         "ruler, military client in olive uniform ONLY when announced by the estado")


def descrever_ancora(png):
    """Gemini descreve o estado REAL da ancora (1 frase EN, objetos + posicoes)."""
    SYS = ("Descreva este frame de claymation como um ESTADO DE CENA em UMA frase em "
           "ingles, objetiva: quem esta onde, o que cada um segura, que objetos existem "
           "e onde estao, estado do piso/agua. Sem interpretacao, so o que se ve. "
           'Responda JSON: {"estado": "uma frase EN"}')
    import base64
    parts = [{"type": "image", "data": base64.b64encode(Path(png).read_bytes()).decode(),
              "mime_type": "image/png"}]
    tx = qc_visao._call(KEY, SYS, parts, max_tokens=400)
    return json.loads(qc_visao._json_de(tx) and __import__("re").search(r"\{.*\}", tx, 16).group(0))["estado"]


def render_com_gate(slug_base, tag, ancora_png, estado_real):
    """Render do clipe com image_start=ancora + AT START=realidade. Retry 1x com seed+1."""
    st_base = json.loads((SETDIR / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
    for tent in range(2):
        slug = slug_base + ("_v2" if tent else "")
        st = dict(st_base)
        st["output_filename"] = slug
        st["seed"] = int(st_base.get("seed", 7001)) + tent
        st["image_start"] = str(ancora_png)
        st["image_prompt_type"] = "S"
        st["prompt"] = (re.sub(r"AT START: (.+?)\. \[Shot",
                               "AT START: " + estado_real.replace("\\", "") + ". [Shot",
                               st_base["prompt"], count=1, flags=16)
                        + ALINHA)
        sdf = SETDIR / (slug + "_settings.json")
        sdf.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n=== %s · tentativa %d · seed %d ===" % (slug, tent + 1, st["seed"]), flush=True)
        t0 = time.time()
        r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", tag + ("" if tent else "")],
                           cwd=CWD)
        mp4s = list(OUT.glob(slug + "*.mp4"))
        print("  render rc=%d · %.1f min" % (r.returncode, (time.time() - t0) / 60), flush=True)
        if r.returncode != 0 or not mp4s:
            continue
        mp4 = mp4s[0]
        # gate do clipe (4 frames vs estado) + gate da ancora de saida
        r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(OUT),
                            "--padrao", slug + "_*.mp4", "--settings", str(SETDIR),
                            "--saida", str(EP / ("qc_" + slug + ".json"))],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout[-500:], flush=True)
        f9 = EP / "refs" / ("ancora_" + slug[-6:] + ".png")
        subprocess.run([FF, "-y", "-ss", "9.9", "-i", str(mp4), "-frames:v", "1", str(f9)],
                       capture_output=True)
        mo = __import__("re").search(r"AT END: (.+?)\.?(?:\n|$)", st_base["prompt"])
        j = qc_visao.gate_ancora(KEY, str(f9), estado=(mo.group(1) if mo else ""), props=PROPS)
        print("  ANCORA SAIDA: %s — %s" % (j.get("veredito"), j.get("motivo", "")), flush=True)
        higiene_ok = (not j.get("personagens_extras")) and (not j.get("objetos_flutuantes")) \
                     and (j.get("dois_bonecos") is not False)
        if higiene_ok:
            return mp4, f9, j
        print("  higiene reprovada — retry", flush=True)
    return None, None, None


import re
ancora = ANCORA_INI
feitos = []
for slug_base, tag in CLIPES:
    est_real = descrever_ancora(ancora)
    print("\n>>> estado REAL da ancora: %s" % est_real, flush=True)
    mp4, f9, j = render_com_gate(slug_base, tag, ancora, est_real)
    if not mp4:
        print("XX %s nao aprovado — cadeia para aqui (regra da serie)." % slug_base, flush=True)
        break
    feitos.append({"slug": slug_base, "mp4": str(mp4), "estado_in_real": est_real,
                   "gate_ancora": j, "ancora_out": str(f9)})
    ancora = f9  # a realidade avanca

(EP / "cadeia_v2_relatorio.json").write_text(json.dumps(feitos, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
print("\n>>> CADEIA V2: %d/%d clipes aprovados — relatorio: cadeia_v2_relatorio.json"
      % (len(feitos), len(CLIPES)), flush=True)
