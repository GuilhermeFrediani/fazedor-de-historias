# -*- coding: utf-8 -*-
"""fix_seam_v7.py — CONSERTO 6 (auditoria 21/11): planos[0] DESCREVE A ANCORA.

Causa-raiz do ghost de 1 s: nos clipes com image_start (ponte), o molde mandava
[Shot 1] como INSERT/close enquanto a imagem de entrada era o WIDE — o modelo
fazia morph do wide para o insert dentro do 1o segundo (double exposure, TEO
duplicado). Correcao: [Shot 1] passa a descrever EXATAMENTE o enquadramento da
ancora e os inserts/planos seguintes nascem datados em >= 0,6 s (nunca em 0,0).

Tambem entra o CONSERTO 8 no texto: sentenca de contagem (EXACTLY ONE bucket...)
para o 2o balde de 15 s nao nascer, e reforco anti-duplicado nos planos de acao.

Uso: python fix_seam_v7.py
"""
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias"
          r"\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"

CONTAGEM = (" There is EXACTLY ONE galvanized bucket on the cart, ONE steel drum moving and "
            "ONE steel grate in this frame - no duplicate object ever appears, no second "
            "bucket and no second telephone.")


def _quebrar(prompt):
    """Separa head (ate o 'AT START:'), meio (AT START..AT END) e tail (soundscape)."""
    i = prompt.find("AT START:")
    j = prompt.rfind("\noverall_soundscape:")
    if i < 0 or j < 0 or j <= i:
        raise SystemExit("prompt fora do formato esperado (sem AT START/ overall_soundscape)")
    head = prompt[:i].rstrip()
    meio = prompt[i:j].rstrip()
    tail = prompt[j:]
    mi = re.search(r"AT START: (.+?)\. \[Shot", meio, flags=16)
    mo = re.search(r"AT END: (.+?)\.?(?:\n|$)", meio, flags=16)
    if not mi or not mo:
        raise SystemExit("prompt sem AT START/AT END parseaveis")
    return head, mi.group(1).strip(), mo.group(1).strip().rstrip("."), tail


def remontar(head, at_start, shots, at_end, tail):
    corpo = " ".join(s.strip() for s in shots)
    return (head + " AT START: " + at_start + ". " + corpo +
            " They do not speak and their mouths do not move, but they breathe, swallow and "
            "react with their whole bodies. AT END: " + at_end + "." + tail)


# ── c01: a ancora de abertura e o WIDE (TEO na parede do telefone a esquerda, JUCA no
#    carrinho a direita, cortina fechada, grelha deitada ao lado do ralo). O molde
#    antigo abria com INSERT do telefone -> morph wide->insert no 1o segundo.
C01_SHOTS = [
    ("[Shot 1] the opening wide frame exactly as established: TEO stands at frame left beside "
     "the wall telephone with its coiled cord looped, JUCA stands at frame right with one hand "
     "resting on the bucket cart handle, the white canvas curtain is closed across the back "
     "with the bare chain and hook hanging above the central drain, and the steel grate lies "
     "face down on the wet floor beside the drain; both puppets hold their positions, "
     "breathing, for the first beat and the military client is NOT visible yet, still hidden "
     "behind the closed curtain."),
    ("[Shot 2] At 00:01.500, the white curtain swings open and the military client in his "
     "olive uniform steps out at frame right, silent, and holds out a folded BLANK white "
     "sheet of paper (completely smooth, no writing, no lines, no marks of any kind); TEO "
     "takes the sheet with both hands; the client points one finger down at the floor drain "
     "to mime the job, then steps back behind the curtain; both heads stay fully inside the "
     "frame."),
    ("[Shot 3] At 00:04.500, the camera cuts to a wide two-shot: TEO tucks the blank sheet "
     "into his flannel chest pocket, lifts the receiver and turns away, the cord snaps taut "
     "and the whole phone box is yanked off the wall and tumbles down onto the fallen steel "
     "grate; JUCA steadies the wobbling bucket cart beside him with one hand and keeps "
     "walking; the client is already gone behind the curtain."),
    ("[Shot 4] At 00:07.000, the camera cuts to a tight two-shot: TEO still holds the "
     "receiver at his ear on a cord that now leads down to a telephone on the floor. He "
     "straightens his spine and raises one flat hand at chest height; JUCA sets the bucket "
     "cart square beside him and both look at the fallen phone box."),
]

# ── c02: a ancora e o close do final do c01 (TEO com o receptor na mao, cordao descendo
#    ate o telefone no chao). O molde antigo abria com INSERT do bota/caster -> morph
#    close->insert no 1o segundo. Insert datado em 00:01.200, com contagem no texto.
C02_SHOTS = [
    ("[Shot 1] the opening tight two-shot held exactly from the previous shot: TEO at frame "
     "left holds the cream telephone receiver at his ear with the coiled cord running down to "
     "the phone box lying face down on the floor beside the fallen steel grate; JUCA at frame "
     "right keeps one hand on the bucket cart; both hold their positions for a beat, "
     "breathing."),
    ("[Shot 2] At 00:01.200, the camera cuts to a close insert of the floor: TEO's military "
     "boot taps twice on the wet concrete beside the cream phone box lying face down by the "
     "drain; then the black casters of a low drum dolly roll into frame and the front caster "
     "rides straight OVER the phone box, flattening and cracking the case under the wheel, "
     "and the dolly keeps rolling." + CONTAGEM),
    ("[Shot 3] At 00:04.500, the camera cuts to a wide shot: the dolly tips over on its side "
     "with the flattened phone box pinned under it, and the empty steel drum rolls off, runs "
     "across the loose steel grate lying by the drain, and the grate settles flat on top of "
     "the rolling drum and stays there; TEO straightens up and points at the hole a beat too "
     "late." + CONTAGEM),
    ("[Shot 4] At 00:07.000, the camera cuts to a wide shot: the drum rolls to the right wall "
     "and stops there with the steel grate balanced on top, the crushed phone box juts out "
     "from under the toppled dolly, and JUCA puts both hands on his knees and follows the "
     "drum with his head." + CONTAGEM),
]

MOLDES = {
    "operacao_ralo_exato_v4_c01_ligacao": C01_SHOTS,
    "operacao_ralo_exato_v4_c02_cadeia": C02_SHOTS,
}

for slug, shots in MOLDES.items():
    arq = SETDIR / (slug + "_settings.json")
    st = json.loads(arq.read_text(encoding="utf-8"))
    head, at_start, at_end, tail = _quebrar(st["prompt"])
    novo = remontar(head, at_start, shots, at_end, tail)
    st["prompt"] = " ".join(novo.split()) if False else novo
    arq.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OK %s: AT START preservado, %d planos (shot 1 = ancora), insertos datados >= 1.2s"
          % (slug, len(shots)))
    print("   shots: " + " | ".join(re.search(r"\[Shot (\d+)\]", s).group(1) for s in shots))