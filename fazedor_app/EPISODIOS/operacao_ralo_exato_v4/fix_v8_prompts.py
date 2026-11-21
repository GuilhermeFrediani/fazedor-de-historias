# -*- coding: utf-8 -*-
# v8: consertos da auditoria da janela 0-19s (molde c01 e c02).
#  - papel da ordem EM BRANCO (zero texto/linhas) + destino (bolso do peito do TEO)
#  - corte seco instruido (sem dissolve/ghost) e ocupacao do cliente explicita
#  - c02: base INTACTA ate a roda do carrinho; a roda causa o racho; grelha vira
#    pelo tambor que rola por cima (causa), nao por magica
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
AL = "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced."
HARD = (" Every cut between shots is a HARD CUT: no dissolve, no cross-fade, no double "
        "exposure, no ghosting, no translucent overlay - only one solid copy of each puppet "
        "in frame.")


def limpar(p):
    p = p.replace(AL, "").strip()
    return re.sub(r"[ \t]{2,}", " ", p)


def troca_shots(p, s1, s2, s3=None):
    p = re.sub(r"\[Shot 1\].*?(?=\[Shot 2\])", s1, p, flags=re.S)
    p = re.sub(r"\[Shot 2\].*?(?=\[Shot 3\])", s2, p, flags=re.S)
    if s3:
        p = re.sub(r"\[Shot 3\].*?(?=AT END:)", s3, p, flags=re.S)
    return p


# ---------------- c01 ----------------
f1 = EP / "settings" / "operacao_ralo_exato_v4_c01_ligacao_settings.json"
d1 = json.loads(f1.read_text(encoding="utf-8"))
p1 = limpar(d1["prompt"])

OCC_OLD = ("Exactly two clay puppets appear in the frame: TEO stays at frame left and JUCA "
           "stays at frame right; no other people or animals appear.")
OCC_NEW = ("TEO stays at frame left and JUCA stays at frame right; in Shot 1 the military client in "
           "his olive uniform steps in from behind the white curtain - exactly ONE solid client, "
           "never a duplicate or a ghost - and leaves; apart from that client no other people or "
           "animals ever appear.")
print("c01 ocupacao encontrada:", OCC_OLD in p1)
p1 = p1.replace(OCC_OLD, OCC_NEW)

SET_TAIL = "Cool hard overhead light, short shadows, wet surfaces."
print("c01 set tail encontrado:", SET_TAIL in p1)
p1 = p1.replace(SET_TAIL, SET_TAIL + HARD)

S1 = ("[Shot 1] Close insert of a white steel wall telephone box bolted at head height, its coiled "
      "cord hanging in a loose loop, and TEO's boots on the wet concrete below; at frame right the "
      "military client in his olive uniform steps in from behind the white curtain and holds out a "
      "folded BLANK paper sheet - plain white paper with absolutely no writing, no lines, no "
      "letters, no symbols, no markings; TEO's hand takes it, folds it once and slides it into his "
      "chest pocket. ")
S2 = ("[Shot 2] At 00:03.500, the camera cuts hard to a wide two-shot: TEO lifts the receiver and "
      "turns away, the cord snaps taut and the whole phone box is yanked off the wall and tumbles "
      "down onto the fallen steel grate, while JUCA steadies the wobbling bucket cart beside him "
      "with one hand and keeps walking; only ONE TEO and ONE JUCA, no overlay. ")
S3 = ("[Shot 3] At 00:07.000, the camera cuts hard to a tight two-shot: TEO still holds the receiver "
      "at his ear on a cord that now leads down to a telephone on the floor. He straightens his "
      "spine and raises one flat hand at chest height; JUCA sets the bucket cart square beside him "
      "and both look at the fallen phone box. They do not speak and their mouths do not move, but "
      "they breathe, swallow and react with their whole bodies; only ONE TEO and ONE JUCA, no ghost. ")
p1 = troca_shots(p1, S1, S2, S3)
d1["prompt"] = p1.strip()
f1.write_text(json.dumps(d1, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------- c02 ----------------
f2 = EP / "settings" / "operacao_ralo_exato_v4_c02_cadeia_settings.json"
d2 = json.loads(f2.read_text(encoding="utf-8"))
p2 = limpar(d2["prompt"])
print("c02 set tail encontrado:", SET_TAIL in p2)
p2 = p2.replace(SET_TAIL, SET_TAIL + HARD)

T1 = ("[Shot 1] Close insert: TEO's military boot taps twice on the wet concrete beside the cream "
      "phone box lying face down by the drain, its bakelite base INTACT and uncracked; at frame "
      "right the black casters of a low drum dolly roll into view. ")
T2 = ("[Shot 2] At 00:03.500, the camera cuts to a wide shot: JUCA pushes the low dolly forward, its "
      "front caster climbs onto the fallen phone base and ONLY THEN the bakelite case cracks with a "
      "sharp snap and flattens under the wheel; the dolly tips over on its side, and the empty steel "
      "drum rolls off across the bay, rolling over the flat steel grate and flipping it flat onto "
      "the drum's top; TEO straightens up and points at the hole a beat too late. ")
T3 = ("[Shot 3] At 00:07.000, the camera cuts to a wide shot: the drum rolls to the right wall and "
      "stops there with the steel grate balanced on top, the crushed phone box juts out from under "
      "the toppled dolly, and JUCA puts both hands on his knees and follows the drum with his head. "
      "They do not speak and their mouths do not move, but they breathe, swallow and react with "
      "their whole bodies. ")
p2 = troca_shots(p2, T1, T2, T3)
p2 = p2.replace("AT END: empty steel drum at rest against the right wall",
                "AT END: empty steel drum at rest against the right wall")
d2["prompt"] = p2.strip()
f2.write_text(json.dumps(d2, indent=2, ensure_ascii=False), encoding="utf-8")

print("\n--- c01 shots ---")
print(p1[p1.find("[Shot 1]"):p1.find("AT END:")])
print("\n--- c02 shots ---")
print(p2[p2.find("[Shot 1]"):p2.find("AT END:")])
