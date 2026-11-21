# -*- coding: utf-8 -*-
"""fix_continuidade_v7.py — CONSERTO da rodada 2 (gate episodico 21/11): continuidade 6 /
causalidade 7. Defeitos REAIS medidos no gate (SYS_A/SYS_B) e corrigidos no molde:

  1) O BALDE some do quadro no c02 (teleporte de objeto sem acao) — coreografia nova:
     o balde sai do carrinho com ACAO (JUCA o pousa no chao) e fica plantado, parado,
     ate o fim do clipe. Nunca troca de dono nem de lugar sozinho.
  2) O PISO seca no c02 (poças do c01 desaparecem) — os planos declaram "the wet floor
     keeps its shallow puddles throughout".
  3) A FOLHA aparece fora do bolso no meio do c01 (com o juiz vendo posse divergente) —
     o guardar acontece DENTRO do plano 2 e o plano 3 comeca com a folha JA no bolso.
  4) EMBLEMA no tambor lido como texto — excecao de registro no PROPS (marca decorativa).
  5) RALO lido como grade instalada — PROPS: "drain hole is not a grate".

Uso: python fix_continuidade_v7.py
"""
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias"
          r"\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"
MOLHADO = (" The wet concrete floor keeps its shallow puddles throughout the whole clip.")

CONTAGEM = (" There is EXACTLY ONE galvanized bucket on the cart, ONE steel drum moving and "
            "ONE steel grate in this frame - no duplicate object ever appears, no second "
            "bucket and no second telephone.")


def _quebrar(prompt):
    i = prompt.find("AT START:")
    j = prompt.rfind("\noverall_soundscape:")
    if i < 0 or j < 0 or j <= i:
        raise SystemExit("prompt fora do formato esperado")
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


# ── c01: a folha e guardada NO plano 2; o plano 3 comeca com ela ja no bolso.
C01_SHOTS = [
    ("[Shot 1] the opening wide frame exactly as established: TEO stands at frame left beside "
     "the wall telephone with its coiled cord looped, JUCA stands at frame right with one hand "
     "resting on the bucket cart handle, the white canvas curtain is closed across the back "
     "with the bare chain and hook hanging above the central drain, and the steel grate lies "
     "face down on the wet floor beside the drain; both puppets hold their positions, "
     "breathing, for the first beat and the military client is NOT visible yet, still hidden "
     "behind the closed curtain." + MOLHADO),
    ("[Shot 2] At 00:01.500, the white curtain swings open and the military client in his "
     "olive uniform steps out at frame right, silent, and holds out a folded BLANK white "
     "sheet of paper (completely smooth, no writing, no lines, no marks of any kind); TEO "
     "takes the sheet with both hands; the client points one finger down at the floor drain "
     "to mime the job, and TEO folds the blank sheet and tucks it into his flannel chest "
     "pocket before the client steps back behind the curtain; both heads stay fully inside "
     "the frame."),
    ("[Shot 3] At 00:04.500, the camera cuts to a wide two-shot with the blank sheet already "
     "tucked inside TEO's chest pocket: TEO lifts the receiver and turns away, the cord snaps "
     "taut and the whole phone box is yanked off the wall and tumbles down onto the fallen "
     "steel grate; JUCA steadies the wobbling bucket cart beside him with one hand and keeps "
     "walking; the client is already gone behind the curtain."),
    ("[Shot 4] At 00:07.000, the camera cuts to a tight two-shot: TEO still holds the "
     "receiver at his ear on a cord that now leads down to a telephone on the floor. He "
     "straightens his spine and raises one flat hand at chest height; JUCA sets the bucket "
     "cart square beside him and both look at the fallen phone box."),
]

# ── c02: coreografia a prova de teleporte — o balde sai do carrinho COM ACAO e fica
#    plantado ao lado do ralo ate o fim; o piso continua molhado; o ralo fica ABERTO.
C02_SHOTS = [
    ("[Shot 1] the opening tight two-shot held exactly from the previous shot: TEO at frame "
     "left holds the cream telephone receiver at his ear with the coiled cord running down to "
     "the phone box lying face down ON TOP of the fallen steel grate at centre — the grate "
     "stays under the box exactly where it fell; JUCA at frame right keeps one hand on the "
     "bucket cart; both hold their positions for a beat, breathing." + MOLHADO),
    ("[Shot 2] At 00:01.200, the camera cuts to a close insert of the floor: JUCA's hands "
     "lift the galvanized bucket off the bucket cart and set it down upright on the wet "
     "concrete beside the drain - the bucket stays planted there and never moves again for "
     "the rest of the shot; then the black casters of the now-empty cart roll into frame and "
     "the front caster rides straight OVER the cream phone box lying on the fallen grate, "
     "flattening and cracking the case under the wheel, and the caster drags the fallen "
     "grate free so it lies loose beside the drain, and the cart keeps rolling." + MOLHADO +
     CONTAGEM),
    ("[Shot 3] At 00:04.500, the camera cuts to a wide shot: the empty cart tips over on its "
     "side with the flattened phone box pinned under it; the steel drum rolls off the cart "
     "bed, runs across the loose steel grate lying beside the drain, and the grate settles "
     "flat on top of the rolling drum; the galvanized bucket stays planted upright beside "
     "the open drain; TEO straightens up and points at the hole a beat too late." + MOLHADO +
     CONTAGEM),
    ("[Shot 4] At 00:07.000, the camera cuts to a wide shot: the drum rolls to the right wall "
     "and stops there with the steel grate balanced flat on top; the galvanized bucket still "
     "sits planted upright beside the open drain; the crushed phone box juts out from under "
     "the toppled cart; and JUCA puts both hands on his knees and follows the drum with his "
     "head." + MOLHADO + CONTAGEM),
]

MOLDES = {
    "operacao_ralo_exato_v4_c01_ligacao": C01_SHOTS,
    "operacao_ralo_exato_v4_c02_cadeia": C02_SHOTS,
}

# AT END atualizado: o balde plantado entra no estado final (o gate compara o frame
# final com esta frase).
AT_END_FIX = {
    "operacao_ralo_exato_v4_c02_cadeia": (
        "empty steel drum at rest against the right wall with the steel grate balanced flat "
        "on top; the galvanized bucket planted upright beside the open drain; client gone; "
        "crushed phone box pinned under the toppled cart"),
}

for slug, shots in MOLDES.items():
    arq = SETDIR / (slug + "_settings.json")
    st = json.loads(arq.read_text(encoding="utf-8"))
    head, at_start, at_end, tail = _quebrar(st["prompt"])
    st["prompt"] = remontar(head, at_start, shots, AT_END_FIX.get(slug, at_end), tail)
    arq.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OK %s: %d planos regravados (coreografia a prova de teleporte)" % (slug, len(shots)))