# -*- coding: utf-8 -*-
"""conserta_prompts_v7.py — cirurgia dos 5 moldes que o proximo render usa.
Mapeia o dossie do usuario (frame a frame) para o texto congelado:

c01  ocupacao AGENDADA + cliente entrega a ordem no Shot 1
c03  trena sai da mao do TEO (lapis AMARELO mede) + queda do plug com arco claro
c04  entrada do rolo de pads PELA ACAO DO JUCA + o MESMO rolo vira travesseiro
     (mata o swap rolo->travesseiro) + pedal fantasma REMOVIDO
c05  lapis AMARELO cravado no gancho como pino (gag que o usuario aprovou)
c06  beat de retirada: tampa do tambor abre -> maleta DENTRO -> so entao nota
     + cliente autorizado no Shot 3 (ocupacao agendada) + ordem causal corrigida
Todos: artefato 'cuts to the camera cuts to' eliminado.
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4\settings")

OCC_ABS = ("Exactly two clay puppets appear in the frame: TEO stays at frame left and JUCA "
           "stays at frame right; no other people or animals appear.")
OCC_CLI = ("TEO and JUCA are the only two main puppets: TEO stays at frame left and JUCA "
           "stays at frame right. The military client in olive uniform appears ONLY in the "
           "shot that names him, silent, no dialogue; no other people or animals appear.")
ART_OLD = "the camera cuts to the camera cuts to"
ART_NEW = "the camera cuts to"

EDITS = {
    "operacao_ralo_exato_v4_c01_ligacao_settings.json": [
        (ART_OLD, ART_NEW, 2),
        (OCC_ABS, OCC_CLI, 1),
        ("[Shot 1] Close insert of a white steel wall telephone box bolted at head height, its "
         "coiled cord hanging in a loose loop, and TEO's boots on the wet concrete below.",
         "[Shot 1] Close insert of a white steel wall telephone box bolted at head height, its "
         "coiled cord hanging in a loose loop, and TEO's boots on the wet concrete below; at "
         "frame right the military client in his olive uniform steps in from behind the white "
         "curtain and holds out a folded paper work order, and TEO's hand takes it from below.",
         1),
    ],
    "operacao_ralo_exato_v4_c03_primeira_falha_v2_settings.json": [
        (ART_OLD, ART_NEW, 2),
        ("with TEO's brass tape hook resting on its front rim.",
         "with a brass tape hook resting loose on its front rim.", 1),
        ("and it bounces down onto TEO's boot, while TEO holds the tape hook out and lock mid-measure.",
         "and it arcs straight back down onto TEO's boot in one clear continuous fall, while TEO "
         "crouches and jabs his YELLOW carpenter pencil at the drain rim, measuring with it.", 1),
        ("rubber test plug swollen and stuck to TEO's boot; drain hole still open; tape measure "
         "clattered on the floor.",
         "rubber test plug swollen and stuck to TEO's boot; drain hole still open; yellow "
         "carpenter pencil in TEO's fist; JUCA's steel tape measure clipped in his chest pocket.", 1),
    ],
    "operacao_ralo_exato_v4_c04_jeitinho_v6a_settings.json": [
        (ART_OLD, ART_NEW, 2),
        ("[Shot 1] Close insert of a roll of white absorbent pads lying on the wet floor beside "
         "a steel floor-wash pedal, and JUCA's clog settling onto that pedal.",
         "[Shot 1] Close insert: JUCA's clog hooks the roll of white absorbent pads out of the "
         "bucket cart and drags it across the wet floor to the drain rim, then stomps flat on "
         "the roll.", 1),
        ("JUCA stamps the wash pedal with his heel, water bursts along the floor and the loose "
         "pads swell into one fat pillow and slide across the concrete",
         "JUCA stamps the rolled pads flat with his heel, water bursts along the floor and that "
         "same roll swells into one fat pillow and slides across the concrete", 1),
        ("A steel pedal clanks down, water bursts along the floor, and soaked pads slap and drag "
         "across the concrete.",
         "Wet padding squelches under a wooden clog, water bursts along the floor, and soaked "
         "pads slap and drag across the concrete.", 1),
    ],
    "operacao_ralo_exato_v4_c05_escalada_v6a_settings.json": [
        ("Close insert of the steel hook swinging gently on its chain, JUCA's fist closing on "
         "the links at the bottom of the frame, the riveted steel wall and a caged lamp filling "
         "the background behind the hook.",
         "Close insert of the steel hook swinging gently on its chain, JUCA's fist closing on "
         "the links at the bottom of the frame and jamming a YELLOW carpenter pencil through "
         "the hook eye like a pin, the riveted steel wall and a caged lamp filling the "
         "background behind the hook.", 1),
        ("steel drum jammed flat against the ceiling plate on the chain; TEO hanging from the "
         "drum with his boots off the wet floor.",
         "steel drum jammed flat against the ceiling plate on the chain; TEO hanging from the "
         "drum with his boots off the wet floor; the yellow carpenter pencil still pinned "
         "through the hook eye.", 1),
    ],
    "operacao_ralo_exato_v4_c06_climax_v6a_settings.json": [
        (OCC_ABS, OCC_CLI, 1),
        ("[Shot 1] Close insert of an open green document case held at chest height, empty "
         "inside, with a military cuff and a brass button beside it.",
         "[Shot 1] Close insert of the steel drum still hanging on the chain, its ridged lid "
         "and brass latch filling the frame, dust flakes drifting down from the steel ceiling "
         "above it.", 1),
        ("water swells up over both pairs of boots and the drum lid spins away flat across the flood.",
         "water swells up over both pairs of boots and the drum lid pops loose, toppling off and "
         "floating flat on the flood.", 1),
        ("TEO lands on his heels and straightens his spine; the military client bends, pinches "
         "a wet blank sheet off the floating lid and lays it in the open case; JUCA puts both "
         "hands on his hips.",
         "TEO lands on his heels, flips the floating drum lid aside and reaches into the open "
         "drum: the green document case sits inside with a wet blank sheet on top; the military "
         "client in olive uniform leans in, pinches the sheet and lays it flat on the case like "
         "a receipt; JUCA puts both hands on his hips.", 1),
        ("drum landed flat sealing the drain; water up over both pairs of boots; empty hook "
         "swaying on the chain draped over the sealed drum; blank sheet in the client's open case.",
         "drum landed flat sealing the drain; water up over both pairs of boots; empty hook "
         "swaying on the chain draped over the sealed drum; the green document case open on the "
         "sealed drum with the blank sheet laid flat on it like a receipt.", 1),
    ],
}

falhas = 0
for nome, trocas in EDITS.items():
    f = S / nome
    st = json.loads(f.read_text(encoding="utf-8"))
    p = st["prompt"]
    print("-" * 90)
    print(nome)
    for velho, novo, esperado in trocas:
        n = p.count(velho)
        marca = "OK " if n == esperado else "XX "
        if n != esperado:
            falhas += 1
        print("  %s %2d/%d  %s" % (marca, n, esperado, velho[:70].replace("\n", " ")))
        p = p.replace(velho, novo)
    st["prompt"] = p
    f.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")

print("-" * 90)
if falhas:
    print("FALHAS: %d — nada gravado onde falhou? (gravado mesmo assim, revisar)" % falhas)
    sys.exit(1)
print("TODAS as trocas casaram — moldes v7 gravados.")
