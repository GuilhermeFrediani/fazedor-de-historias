# -*- coding: utf-8 -*-
"""fix_ancora_v7.py — nova ANCORA DE ABERTURA com a porta de aco (sem cortina).

A ancora antiga (refs/ancora_v7_abertura.png) tem a cortina + a faixa de ceu — que era
justamente a deixa que fazia o H3 render exterior atras dela. A nova ancora e um wide
estatico do galpao com a PORTA DE ACO FECHADA no fundo, ultimo frame de um draft de 5 s
com o SET novo (a mesma receita do gerar_keyframe). Gate de visao antes de aceitar.

Uso: python fix_ancora_v7.py
"""
import json, re, subprocess, sys
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias"
          r"\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
import qc_visao

KEY = qc_visao._chave()
src = (EP / "cadeia_v7.py").read_text(encoding="utf-8")
PROPS = eval(re.search(r"PROPS = \(.*?\)\n", src, flags=re.S).group(0).split("=", 1)[1].strip())
mo_set = re.search(r"SET_NOVO = \((.*?)\)\n", src, flags=re.S)
SET_NOVO = eval("(" + mo_set.group(1) + ")")

SLUG = "operacao_ralo_exato_v4_c01_ligacao"
base = json.loads((EP / "settings" / (SLUG + "_settings.json")).read_text(encoding="utf-8"))
head = base["prompt"][:base["prompt"].find("AT START:")].rstrip()
# troca_set igual ao da cadeia: substitui o bloco de SET do molde-base pelo SET_NOVO
head = re.sub(r"a small military vehicle-wash bay.*?wet surfaces\.", SET_NOVO, head, flags=16)

ESTADO = ("TEO stands at frame left beside the wall telephone, JUCA stands at frame right "
          "with one hand on the bucket cart handle, a steel drum stands at the rear right "
          "corner, a RIBBED STEEL ROLL-UP DOOR is closed at the back against the riveted "
          "rear steel wall, the bare chain and hook hang above the central drain, the steel "
          "grate lies face down on the wet floor beside the drain, and the military client "
          "is not visible yet. The bay interior fills the whole frame edge to edge with "
          "riveted steel walls and roof.")
PROMPT = (head + " AT START: " + ESTADO + ". [Shot 1] a static wide two-shot of the whole "
          "bay: TEO at frame left beside the wall telephone and JUCA at frame right with "
          "one hand on the bucket cart; both breathe and hold their positions. AT END: the "
          "same wide frame, unchanged. They do not speak and their mouths do not move, but "
          "they breathe, swallow and react with their whole bodies."
          "\noverall_soundscape: room tone of the enclosed bay, a low hum of the caged "
          "lamps, water dripping slowly.\nnon_diegetic_music: N/A")

st = dict(base)
st["output_filename"] = "ancora_v7_porta"
st["video_length"] = "5s"
st["seed"] = 7001
st.pop("image_start", None)
st["prompt"] = PROMPT
sdf = EP / "settings" / "ancora_v7_porta_settings.json"
sdf.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
print("  draft da nova ancora (5 s, seed 7000)...", flush=True)
r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", "V7_ANCP"], cwd=CWD)
cands = [p for p in OUT.glob("ancora_v7_porta*.mp4")]
if r.returncode != 0 or not cands:
    raise SystemExit("draft falhou rc=%d" % r.returncode)
mp4 = max(cands, key=lambda p: p.stat().st_mtime)
dest = EP / "refs" / "ancora_v7_porta.png"
subprocess.run([FF, "-y", "-ss", "4.4", "-i", str(mp4), "-frames:v", "1", str(dest)],
               capture_output=True)
print("  ancora extraida:", dest)
j = qc_visao.gate_ancora(KEY, str(dest), estado=ESTADO, props=PROPS, cliente=False)
print("  GATE ANCORA: %s - %s" % (j.get("veredito"), j.get("motivo", "")))
print("  cenario=%s nao_plantados=%s" % (j.get("cenario_violado"), j.get("objetos_nao_plantados")))
if j.get("veredito") != "APROVADA":
    raise SystemExit("ancora reprovada — ajuste antes de relancar")
print(">>> nova ancora APROVADA: " + str(dest))
