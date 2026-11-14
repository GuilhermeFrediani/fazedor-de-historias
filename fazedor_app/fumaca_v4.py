# -*- coding: utf-8 -*-
"""
FUMAÇA v4 — 6 clipes consecutivos de "OPERAÇÃO RALO EXATO".
Cada clipe tem 3 planos com corte datado (inserto -> ação -> reação de corpo),
som concreto + som de boca, e uma cama musical de comédia.
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR.parent))
import fazedor_app as F

SLUG = "operacao_ralo_exato_v4"

SET = (
    "SET: a small military vehicle-wash bay of riveted grey steel plates. Wet grey concrete "
    "floor, two faded yellow safety lines, one rectangular drain hole at centre with the grate "
    "lying face down beside it, red-wheel water valves and a coiled hose reel on the left wall, "
    "electric cabinets and a broom on the right wall, two stacked steel drums at rear right, a "
    "white canvas curtain on a ceiling rail at the back, a bare chain with a hook above the "
    "drain, two caged industrial lamps. Cool hard overhead light, short shadows, wet surfaces."
)
MUS = "N/A"   # CANON: ZERO MÚSICA — o foley é o punchline (LEI DE FERRO nº 3 do dossiê v1)

CLIPES = [
 {"n": 1, "dur": 10, "estagio": "LIGACAO",
  "estado_in": "white phone box bolted on the left wall with its coiled cord looped; steel grate lying face-down on the floor beside the drain; floor dry",
  "estado_out": "phone box torn off the wall and lying on the fallen grate; receiver still in TEO's hand on the cord; a military boot stepping in behind the curtain",
  "planos": [
    {"t": "00:00.000", "texto": ("Close insert of a white steel wall telephone box bolted at head "
      "height, its coiled cord hanging in a loose loop, and TEO's boots on the wet concrete below.")},
    {"t": "00:03.500", "texto": ("the camera cuts to a wide two-shot: TEO lifts the receiver and turns "
      "away, the cord snaps taut and the whole phone box is yanked off the wall and tumbles down onto "
      "the fallen steel grate, while JUCA shoulders a steel drum past behind him and keeps walking.")},
    {"t": "00:07.000", "texto": ("the camera cuts to a tight two-shot: TEO still holds the receiver at "
      "his ear on a cord that now leads down to a telephone on the floor. He straightens his spine and "
      "raises one flat hand at chest height; behind him the white curtain slides and a military boot "
      "steps into the bay.")}],
  "gag": "o fio do telefone e curto: TEO se afasta e a caixa inteira sai da parede e cai na grelha.",
  "objeto_gag": "caixa do telefone", "fisica": "tombar",
  "reacao": "TEO endireita a coluna de repente, ergue uma mao aberta na altura do peito e alisa o bigode devagar; JUCA encolhe os ombros e trava o passo com o tambor nas costas.",
  "som": "estalo de baquelite; fio esticando; caixa de aco batendo no concreto; grelha retinindo; resfolego do TEO; suspiro do JUCA",
  "overall_soundscape": ("A bakelite receiver clicks off its cradle, the coiled cord creaks as it "
    "tightens, and the steel phone box bangs down on the concrete and rings. TEO snorts one short "
    "nasal breath. JUCA exhales a long flat sigh."),
  "non_diegetic_music": MUS},

 {"n": 2, "dur": 10, "estagio": "CHEGADA",
  "estado_in": "phone box torn off the wall and lying on the fallen grate; receiver still in TEO's hand on the cord; a military boot stepping in behind the curtain",
  "estado_out": "empty steel drum rolling across the bay with the steel grate balanced flat on top; client gone; phone box crushed under the toppled dolly",
  "planos": [
    {"t": "00:00.000", "texto": ("Close insert of a military boot tapping twice on the wet floor "
      "beside the fallen phone box, a green document case swinging at the edge of frame.")},
    {"t": "00:03.500", "texto": ("the camera cuts to a wide shot: JUCA rolls a low drum dolly at the "
      "open hole, one caster rides up onto the fallen phone box and the dolly tips, and the empty "
      "steel drum tumbles off across the bay with the steel grate balanced flat on its top, while "
      "TEO straightens up and points at the hole a beat too late.")},
    {"t": "00:07.000", "texto": ("the camera cuts to a medium shot: TEO holds the point with one arm "
      "out and lowers it slowly; JUCA puts both hands on his knees and turns his head to follow the "
      "rolling drum, then pulls the pencil from behind his ear.")}],
  "gag": "a rodinha do carrinho sobe no telefone caido, o tambor desce sozinho e sai rolando com a grelha equilibrada em cima como uma tampa.",
  "objeto_gag": "tambor de aco", "fisica": "rolar", "herda_de": "phone box",
  "reacao": "JUCA apoia as duas maos nos joelhos, gira a cabeca seguindo o tambor e puxa o lapis de tras da orelha; TEO segura o braco esticado no ar e o abaixa devagar.",
  "som": "bota militar batendo no concreto; rodinha raspando em baquelite; tambor oco rolando; grelha raspando no tambor; resfolego curto; estalo de lingua",
  "overall_soundscape": ("A military boot taps twice on wet concrete, then the dolly caster scrapes "
    "over the bakelite phone box and the hollow steel drum rolls away with a low rumble. TEO makes "
    "one short nasal snort. JUCA clicks his tongue once."),
  "non_diegetic_music": MUS},

 {"n": 3, "dur": 10, "estagio": "PRIMEIRA_FALHA",
  "estado_in": "empty steel drum rolling across the bay with the steel grate balanced flat on top; client gone; phone box crushed under the toppled dolly",
  "estado_out": "rubber test plug swollen and stuck to TEO's boot; drain hole still open; tape measure clattered on the floor",
  "planos": [
    {"t": "00:00.000", "texto": ("Close insert of the open drain throat, a black rectangular hole in "
      "the wet concrete, with TEO's brass tape hook resting on its front rim.")},
    {"t": "00:03.500", "texto": ("the camera cuts to a wide shot: JUCA stamps an oversized rubber test "
      "plug into the hole with his heel, the rubber swells past the rim and fires the plug straight "
      "up, and it bounces down onto TEO's boot, while TEO holds the tape hook out and lock "
      "mid-measure.")},
    {"t": "00:07.000", "texto": ("the camera cuts to a low two-shot: TEO lifts that boot off the floor "
      "with the swollen plug stuck to it like a slipper and holds the raised knee; JUCA leans in with "
      "both hands on his thighs to look at it too.")}],
  "gag": "o tampao de teste incha mais que o buraco, sai voando como rolha e cai justo no pe do TEO.",
  "objeto_gag": "tampao de borracha", "fisica": "inflar", "herda_de": "steel grate",
  "reacao": "TEO levanta a bota do chao com o tampao grudado, dobra o joelho e segura a perna no ar; JUCA se inclina com as maos nas coxas e assente devagar.",
  "som": "borracha comprimida pelo calcanhar; estalo de ar; tampao batendo na bota; trena caindo no piso; resfolego; suspiro",
  "overall_soundscape": ("Rubber squeaks against the concrete rim, a wet pop fires the plug upward, "
    "and it slaps onto a leather boot while a tape measure clatters down. TEO huffs once through his "
    "nose. JUCA lets out a low sigh."),
  "non_diegetic_music": MUS},

 {"n": 4, "dur": 10, "estagio": "JEITINHO",
  "estado_in": "rubber test plug swollen and stuck to TEO's boot; drain hole still open; tape measure clattered on the floor",
  "estado_out": "soaked absorbent pad swollen into a fat pillow covering both of TEO's boots; floor wetter; drain still open",
  "planos": [
    {"t": "00:00.000", "texto": ("Close insert of a roll of white absorbent pads lying on the wet "
      "floor beside a steel floor-wash pedal, and JUCA's clog settling onto that pedal.")},
    {"t": "00:03.500", "texto": ("the camera cuts to a wide shot: JUCA stamps the wash pedal with his "
      "heel, water bursts along the floor and the loose pads swell into one fat pillow and slide "
      "across the concrete, while TEO crouches down and grabs at the edge of the sliding pillow with "
      "both hands.")},
    {"t": "00:07.000", "texto": ("the camera cuts to a low two-shot: the swollen pillow stops over "
      "TEO's boots and swallows them; TEO lifts one foot and the whole pad lifts with it; JUCA wipes "
      "both hands down his trousers.")}],
  "gag": "as mantas bebem toda a agua, incham como um travesseiro e engolem as duas botas do TEO.",
  "objeto_gag": "mantas absorventes", "fisica": "transbordar", "herda_de": "rubber test plug",
  "reacao": "TEO ergue um pe e a manta inteira sobe junto, dobra o joelho e olha para o proprio pe; JUCA limpa as duas maos na calca e assente com a cabeca.",
  "som": "pedal de aco batendo; agua jorrando pelos bicos; mantas encharcadas arrastando; botas sugadas; resfolego; estalo de lingua",
  "overall_soundscape": ("A steel pedal clanks down, water bursts along the floor, and soaked pads "
    "slap and drag across the concrete. TEO snorts. JUCA clicks his tongue twice."),
  "non_diegetic_music": MUS},

 {"n": 5, "dur": 10, "estagio": "ESCALADA",
  "estado_in": "soaked absorbent pad swollen into a fat pillow covering both of TEO's boots; floor wetter; drain still open",
  "estado_out": "steel drum jammed flat against the ceiling plate on the chain; TEO hanging from the drum with his boots off the wet floor",
  "planos": [
    {"t": "00:00.000", "texto": ("Close insert of a steel hook hanging on a chain directly above the "
      "open drain, swinging gently, empty, with JUCA's hand reaching up into frame.")},
    {"t": "00:03.500", "texto": ("the camera cuts to a wide shot: JUCA hauls the chain down hand over "
      "hand and the steel drum swings up and jams flat against the ceiling plate, while TEO shoves "
      "both palms up under it and pushes.")},
    {"t": "00:07.000", "texto": ("the camera cuts to a medium shot: TEO grips the hanging drum with "
      "both hands and pulls, and his own boots come up off the wet floor while JUCA holds the chain "
      "still with one hand and shrugs.")}],
  "gag": "JUCA ergue o tambor na corrente e ele trava no teto; TEO puxa o tambor e e o TEO que sobe.",
  "objeto_gag": "tambor de aco na corrente", "fisica": "escorregar",
  "reacao": "TEO fica pendurado com as duas maos no tambor, as botas balancando no ar, e olha para os proprios pes; JUCA dobra o pescoco para tras e apoia as maos na cintura.",
  "som": "corrente raspando no gancho; tambor batendo no teto de aco; corrente esticando; botas raspando no ar; resfolego; assobio baixo",
  "overall_soundscape": ("The chain rasps through the hook and the steel drum clangs against the "
    "ceiling plate, then the chain creaks under a new weight. TEO grunts once. JUCA whistles two "
    "low flat notes."),
  "non_diegetic_music": MUS},

 {"n": 6, "dur": 10, "estagio": "CLIMAX",
  "estado_in": "steel drum jammed flat against the ceiling plate on the chain; TEO hanging from the drum with his boots off the wet floor",
  "estado_out": "drum landed flat sealing the drain; water up over both pairs of boots; blank sheet in the client's open case",
  "planos": [
    {"t": "00:00.000", "texto": ("Close insert of an open green document case held at chest height, "
      "empty inside, with a military cuff and a brass button beside it.")},
    {"t": "00:03.500", "texto": ("the camera cuts to a wide shot: JUCA lets the chain slip and TEO "
      "drops with it, the drum lands flat on the open drain and seals it, water swells up over both "
      "pairs of boots and the drum lid spins away flat across the flood.")},
    {"t": "00:07.000", "texto": ("the camera cuts to a medium two-shot: TEO lands on his heels and "
      "straightens his spine; the military client bends, pinches a wet blank sheet off the floating "
      "lid and lays it in the open case; JUCA puts both hands on his hips.")}],
  "gag": "a corrente escapa, o tambor cai e sela o buraco; a agua sobe e a nota sai do chao molhada.",
  "objeto_gag": "tambor de aco", "fisica": "tombar", "herda_de": "steel drum",
  "reacao": "TEO aterrissa nos calcanhares, endireita a coluna e olha a agua nas botas; JUCA apoia as duas maos na cintura e olha para o teto; o cliente fecha a pasta devagar.",
  "som": "corrente escapando; tambor batendo seco no concreto; agua subindo; tampa girando na agua; papel molhado; suspiro longo; estalo de lingua",
  "overall_soundscape": ("The chain slips with a sharp clack, the drum lands flat on the drain with a "
    "deep boom, and water laps up over leather boots. A wet sheet of paper peels off the metal. TEO "
    "exhales a long sigh and JUCA clicks his tongue once."),
  "non_diegetic_music": MUS},
]

EP = {
  "titulo": "OPERAÇÃO RALO EXATO (v4)",
  "logline": ("TEO mede o ralo errado e JUCA o sela com o tampao errado; o tambor acaba no teto, o "
    "piso alaga e a dupla entrega o servico mesmo assim."),
  "setor": "deposito militar de manutencao industrial",
  "servico": "lavagem pressurizada do box antes de uma inspecao",
  "cliente": "encarregado militar mudo",
  "mecanismo": ("o tampao pneumatico de teste, parecido com uma cabeca de limpeza, veda o ralo em vez "
    "de limpa-lo, e a agua de lavagem volta toda para o piso"),
  "degrau_final": "teto e piso: o tambor sobe na corrente e cai selando o buraco",
  "objetos_plantados": [
    {"objeto": "caixa do telefone", "plantado_no_clipe": 1, "pago_no_clipe": 2},
    {"objeto": "grelha de aco", "plantado_no_clipe": 1, "pago_no_clipe": 2},
    {"objeto": "tambor de aco", "plantado_no_clipe": 2, "pago_no_clipe": 6},
    {"objeto": "tampao de borracha", "plantado_no_clipe": 3, "pago_no_clipe": 4},
    {"objeto": "mantas absorventes", "plantado_no_clipe": 4, "pago_no_clipe": 5}],
  "callback_object": "tambor de aco",
  "set_historia": SET,
  "continuidade": [
    "TEO a esquerda com a trena; JUCA a direita executando",
    "o telefone fica no chao do clipe 1 ao 2 e nao volta para a parede",
    "a grelha sai do ralo no clipe 1 e volta no clipe 2, em cima do tambor",
    "o buraco do ralo fica aberto do clipe 2 ao 5 e e selado no 6",
    "a agua cresce: seco (1-2) -> molhado (3-4) -> alagado (5-6)",
    "o cliente aparece na cortina no clipe 1 e volta no 6"],
  "assinatura": "nota fiscal em branco, molhada, sai da tampa do tambor e entra na pasta do cliente",
  "shots": CLIPES,
}

pasta = F.EPISODIOS_DIR / SLUG
sdir = pasta / "settings"
sdir.mkdir(parents=True, exist_ok=True)
(pasta / "episodio.json").write_text(json.dumps(EP, ensure_ascii=False, indent=2), encoding="utf-8")

r = F.validar_dossie(EP)
print("=" * 78)
print("VALIDACAO v4 —", EP["titulo"])
print("=" * 78)
print("NOTA: %s/10  · humor %s · render %s · montage %s"
      % (r.get("nota"), r.get("humor"), r.get("render"), r.get("montage")))
for c in r.get("checks_render", []) + r.get("checks_montage", []):
    print("  ok -", c)
for w in r.get("avisos", []):
    print("  AVISO ", w)
for e in r.get("erros", []):
    print("  ERRO  ", e)
print("=" * 78)

arquivos = []
for s in CLIPES:
    cfg = dict(F.TEMPLATE_SETTINGS)
    cfg["video_length"] = "10s"
    cfg["output_filename"] = "%s_c%02d_%s" % (SLUG, s["n"], s["estagio"].lower())
    cfg["prompt"] = F.prompt_dossie(s, EP)
    arq = sdir / (cfg["output_filename"] + "_settings.json")
    arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    arquivos.append(arq)
    print("settings: %s · prompt %d chars · %d planos"
          % (arq.name, len(cfg["prompt"]), len(s["planos"])))

print("\n%d erro(s) · %d aviso(s)" % (len(r.get("erros", [])), len(r.get("avisos", []))))
if r.get("erros"):
    sys.exit(1)
print("--seco: settings escritos, 0 GPU gasta. pronto para render.")
