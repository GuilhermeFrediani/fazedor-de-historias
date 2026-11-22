# -*- coding: utf-8 -*-
"""fix_round3_v7.py — RODADA 3 (auditoria do usuario sobre os 20 s, 21/11 a noite):

  1) FUNDO-EXTERIOR atras da cortina (ceu + arvores em 2-4 s): o SET agora declara o que
     existe atras da cortina — a parede de aco rebitada do PROPRIO galpao. Nunca ceu,
     arvores ou exterior. O cliente sai de TRAS da cortina (ela o esconde), nao de um mundo
     exterior.
  2) BALDE DUPLICADO no c02 (14-19 s): coreografia reforcada — o balde galvanizado NAO e
     um tambor e NUNCA rola: fica plantado, parado, ao lado do ralo, do momento em que o
     JUCA o pousa ate o fim do clipe. So o TAMBOR de aco rola.
  3) BORROES de rosto/olhos: num_inference_steps 6 -> 8 em todos os moldes (o LoRA turbo
     e de 8 passos; rodar com 6 degrada detalhe fino de rosto).
  4) LINGUA DO TEO (drift de tique): a reacao atribui lingua/boina ao JUCA e
     bigode/coluna/palma ao TEO — tique trocado vira erro de personagem.
  5) BARRIL sem plantio: o tambor de aco fica visivel no canto direito desde o plano 1 do
     c01 (plantio no wide de abertura).

Uso: python fix_round3_v7.py
"""
import json, re
from pathlib import Path

EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias"
          r"\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"
MOLHADO = (" The wet concrete floor keeps its shallow puddles throughout the whole clip.")
CONTAGEM = (" There is EXACTLY ONE galvanized bucket on the cart, ONE steel drum moving and "
            "ONE steel grate in this frame - no duplicate object ever appears, no second "
            "bucket and no second telephone. The BLANK white sheet stays perfectly smooth "
            "with no writing, no lines and NO mark of any kind at any moment - no pen mark "
            "ever appears on it.")


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


C01_SHOTS = [
    ("[Shot 1] the opening wide frame exactly as established: TEO stands at frame left beside "
     "the wall telephone with its coiled cord looped, JUCA stands at frame right with one hand "
     "resting on the bucket cart handle, a steel drum stands planted at the rear right corner "
     "of the bay, the RIBBED STEEL ROLL-UP DOOR is closed at the back against the bay's own "
     "riveted rear steel wall, the bare chain and hook hang above the central drain, and the "
     "steel grate lies face down on the wet floor beside the drain; both puppets hold their "
     "positions, breathing, for the first beat and the military client is NOT visible yet, "
     "still hidden behind the closed curtain." + MOLHADO),
    ("[Shot 2] At 00:01.500, the military client in his olive uniform steps INTO the frame "
     "from frame right, arriving from the side of the closed ribbed steel roll-up door, and "
     "holds out a folded BLANK white sheet of paper (completely smooth, no writing, no "
     "lines, no marks of any kind); the closed ribbed steel door with the bay's own riveted "
     "steel wall fills the background; TEO "
     "takes the sheet with both hands; the client points one finger down at the floor drain "
     "to mime the job, and TEO folds the blank sheet and tucks it into his flannel chest "
     "pocket before the client steps back out of frame; both heads stay fully inside the "
     "frame."),
    ("[Shot 3] At 00:04.500, the camera cuts to a wide two-shot with the blank sheet already "
     "tucked inside TEO's chest pocket: TEO lifts the receiver and turns away, the cord snaps "
     "taut and the whole phone box is yanked off the wall and tumbles down onto the fallen "
     "steel grate; JUCA steadies the wobbling bucket cart beside him with one hand and keeps "
     "walking; the client is already gone behind the curtain."),
    ("[Shot 4] At 00:07.000, the camera cuts to a tight two-shot: TEO still holds the "
     "receiver at his ear on a cord that now leads down to a telephone on the floor. He "
     "straightens his spine, smooths his walrus moustache once and raises one flat hand at "
     "chest height - TEO never sticks his tongue out, the tongue tic belongs to JUCA alone; "
     "JUCA sets the bucket cart square beside him, adjusts his flat cap and lets his tongue "
     "slip out slightly, and both look at the fallen phone box."),
]

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
     "side with the flattened phone box pinned under it; ONLY the empty steel drum rolls - "
     "the galvanized bucket is NOT a drum and never rolls, it stays planted upright beside "
     "the drain; the steel drum runs across the loose steel grate lying beside the drain, "
     "and the grate settles flat on top of the rolling drum; TEO straightens up and points "
     "at the hole a beat too late." + MOLHADO + CONTAGEM),
    ("[Shot 4] At 00:07.000, the camera cuts to a wide shot: the steel drum rolls to the "
     "right wall and stops there with the steel grate balanced flat ON TOP OF THE DRUM (never "
     "on the bucket); the galvanized bucket still sits planted upright beside the open drain, "
     "untouched; the crushed phone box juts out from under the toppled cart; and JUCA puts "
     "both hands on his knees, adjusts his flat cap and lets his tongue slip out slightly - "
     "the tongue tic belongs to JUCA alone." + MOLHADO + CONTAGEM),
]

MOLDES = {
    "operacao_ralo_exato_v4_c01_ligacao": C01_SHOTS,
    "operacao_ralo_exato_v4_c02_cadeia": C02_SHOTS,
}

for slug, shots in MOLDES.items():
    arq = SETDIR / (slug + "_settings.json")
    st = json.loads(arq.read_text(encoding="utf-8"))
    head, at_start, at_end, tail = _quebrar(st["prompt"])
    st["prompt"] = remontar(head, at_start, shots, at_end, tail)
    # CONSERTO 3: o LoRA turbo e de 8 passos; rodar com 6 degrada rosto/olhos.
    st["num_inference_steps"] = 8
    arq.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OK %s: %d planos regravados + steps=8" % (slug, len(shots)))

