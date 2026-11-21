# -*- coding: utf-8 -*-
# Consertos do c01 conforme auditoria 0-19s:
#  - papel 100% EM BRANCO (lei zero-texto) + mímica (apontar o ralo)
#  - destino do papel: TEO guarda no bolso do peito (delta de posse)
#  - cortes secos: proibido dissolve/ghost/morph/figura duplicada
#  - cabeças completas no insert
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
f = EP / "settings" / "operacao_ralo_exato_v4_c01_ligacao_settings.json"
d = json.loads(f.read_text(encoding="utf-8"))
p = d["prompt"]

AL = "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced."
p = p.replace(AL, "").strip()
p = re.sub(r"[ \t]{2,}", " ", p)

CORTE = ("All transitions between shots are INSTANT HARD CUTS on the exact cut timestamps: "
         "no cross-dissolve, no fade, no double exposure, no translucent ghost figures, no "
         "duplicated characters, no morphing between poses. ")

NEW1 = ("[Shot 1] Close insert of a white steel wall telephone box bolted at head height, its coiled "
        "cord hanging in a loose loop, and TEO's boots on the wet concrete below; at frame right the "
        "military client in his olive uniform steps in from behind the white curtain and holds out a "
        "folded BLANK white sheet of paper (completely smooth, no writing, no lines, no marks of any "
        "kind) and TEO's hand takes it from below; the client points one finger at the floor drain to "
        "mime the job; both heads stay fully inside the frame. ")
NEW2 = ("[Shot 2] At 00:03.500, the camera cuts to a wide two-shot: TEO tucks the blank sheet into his "
        "flannel chest pocket, lifts the receiver and turns away, the cord snaps taut and the whole "
        "phone box is yanked off the wall and tumbles down onto the fallen steel grate, while JUCA "
        "steadies the wobbling bucket cart beside him with one hand and keeps walking; the client has "
        "already stepped back behind the curtain. ")

p = re.sub(r"\[Shot 1\].*?(?=\[Shot 2\])", NEW1, p, flags=re.S)
p = re.sub(r"\[Shot 2\].*?(?=\[Shot 3\])", NEW2, p, flags=re.S)
if "INSTANT HARD CUTS" not in p:
    p = p.replace("AT START:", CORTE + "AT START:", 1)
p = re.sub(r"[ \t]{2,}", " ", p)

d["prompt"] = p
f.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

print("--- c01 consertado ---")
print(p[p.find("AT START:"):][:1200])
