# -*- coding: utf-8 -*-
# c02 v2 conforme auditoria 0-19s:
#  - causa do esmagamento VISIVEL no insert (caster passa por cima da base)
#  - grade com causa (o tambor passa por cima dela e ela assenta em cima do tambor)
#  - cortes secos; AT END com estado verificavel (tambor parado na parede direita)
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
f = EP / "settings" / "operacao_ralo_exato_v4_c02_cadeia_settings.json"
d = json.loads(f.read_text(encoding="utf-8"))
p = d["prompt"]

AL = "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced."
p = p.replace(AL, "").strip()
p = re.sub(r"[ \t]{2,}", " ", p)

CORTE = ("All transitions between shots are INSTANT HARD CUTS on the exact cut timestamps: "
         "no cross-dissolve, no fade, no double exposure, no translucent ghost figures, no "
         "duplicated characters, no morphing between poses. ")

NEW1 = ("[Shot 1] Close insert: TEO's military boot taps twice on the wet concrete beside the cream "
        "phone box lying face down by the drain; then the black casters of a low drum dolly roll into "
        "frame and the front caster rides straight OVER the phone box, flattening and cracking the "
        "case under the wheel, and the dolly keeps rolling. ")
NEW2 = ("[Shot 2] At 00:03.500, the camera cuts to a wide shot: the dolly tips over on its side with "
        "the flattened phone box pinned under it, and the empty steel drum rolls off, runs across the "
        "loose steel grate lying by the drain, and the grate settles flat on top of the rolling drum; "
        "TEO straightens up and points at the hole a beat too late. ")
NEW3 = ("[Shot 3] At 00:07.000, the camera cuts to a wide shot: the drum rolls to the right wall and "
        "stops there with the steel grate balanced on top, the crushed phone box juts out from under "
        "the toppled dolly, and JUCA puts both hands on his knees and follows the drum with his head. "
        "They do not speak and their mouths do not move, but they breathe, swallow and react with "
        "their whole bodies. ")
NEW_END = ("AT END: empty steel drum at rest against the right wall with the steel grate balanced "
           "flat on top; client gone; crushed phone box pinned under the toppled dolly.")

p = re.sub(r"\[Shot 1\].*?(?=\[Shot 2\])", NEW1, p, flags=re.S)
p = re.sub(r"\[Shot 2\].*?(?=\[Shot 3\])", NEW2, p, flags=re.S)
p = re.sub(r"\[Shot 3\].*?(?=AT END:)", NEW3, p, flags=re.S)
p = re.sub(r"AT END: [^\n]*", NEW_END, p, count=1)
if "INSTANT HARD CUTS" not in p:
    p = p.replace("AT START:", CORTE + "AT START:", 1)
p = re.sub(r"[ \t]{2,}", " ", p)

d["prompt"] = p
f.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

print("--- c02 consertado ---")
print(p[p.find("[Shot 1]"):][:1100])
