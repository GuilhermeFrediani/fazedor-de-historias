# -*- coding: utf-8 -*-
"""FUMAÇA DE COMÉDIA (1 min) — 6 clipes do arco de CARGA MÁXIMA, transcritos do gerador.
#5 #7 #11 #15 #21 #25 → gen_test ×6 → concat."""
import json, io, os, subprocess, sys, time, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
import fazedor_app as F

SLUG = "carga_maxima"
STYLE = ("Claymation plasticine stop-motion style. Handcrafted modelling clay puppets with "
         "visible fingerprints, tool marks and thumb-pressed texture, matte with gentle satin "
         "sheen, photographed on a miniature practical set. Artifacts: miniature seams, "
         "fingerprint ridges and real dust.")
SET = ("SET: interior of a decommissioned industrial loading hall. Grey concrete floor, faded "
       "yellow loading line, riveted steel columns, high frosted windows, exposed roof beams, "
       "three painted rack footprints, timber parts crates and a pallet jack. Cool diffuse "
       "overcast daylight, soft short shadows.")
JUCA = ("Claymation character JUCA, a Black handyman, 22cm puppet, 3.5 heads tall. Barrel "
        "torso, short stubby legs, oversized clay hands with four thick sausage fingers, small "
        "round ears. Slightly flattened spherical head. Dark warm brown matte clay skin #6B4226 "
        "with fingerprint texture. Short cropped hair built from many small black clay coils "
        "#1A1512, straight hairline, covering the crown and 1.5cm down the temples. Large "
        "bulbous terracotta round nose #8F4E33 projecting forward. Eyes: two small black clay "
        "dots 4mm, no sclera, one tiny white highlight each. Black clay eyebrows angled "
        "slightly inward. Mouth: single thin dark-brown clay line, gentle upward curve, faint "
        "lips, no teeth. Small jowls. Mustard knitted clay sweater #C98A2E with sculpted cable "
        "ribbing, round ribbed collar, ribbed cuffs and hem, grey-blue patch on left elbow; "
        "olive-green twill trousers #4E5A3C, marked seam, frayed rolled cuff; pale wooden "
        "clogs #C9A46B with brown leather strap; burnt-brown clay flat cap #6E3B22 tilted "
        "right, short brim; coiled yellow measuring tape #E8C23A from the trouser pocket; "
        "carpenter pencil behind right ear.")
TEO = ("Claymation character TÉO, a white handyman, 24cm puppet, 3.8 heads tall, slim, "
       "slightly stooped. Narrow cylindrical torso, long thin limbs, oversized clay hands with "
       "four long slim fingers, protruding oval ears. Elongated oval head, broad forehead. Pale "
       "pinkish matte clay skin #EFC6A8. Bald smooth crown with subtle satin sheen #F0C9AB, two "
       "tufts of straw-blond clay hair #D9B26A above the ears, deep receding hairline. "
       "Pear-shaped nose with drooping tip, light terracotta #D98E6B. Eyes: two small black "
       "clay dots 4.5mm, no sclera, one tiny white highlight each. Straw-blond clay eyebrows "
       "arched outward. Large straw-blond clay moustache #C9A97A, 3.4cm wide, covering the "
       "whole upper lip, ends drooping below the mouth line; mouth hidden underneath, no teeth. "
       "Red and black checked flannel clay shirt #A8322A / #2B2320, small checks, pointed "
       "collar, five cream buttons, sleeves rolled twice; brown leather-look suspenders #5A3A22 "
       "with small brass buckles; khaki trousers #8C7A54, straight hem; dark brown lace-up "
       "boots #3E2A1C; teal knitted beanie #2F4F5E with two cream stripes #EFE4CE, folded "
       "twice, no pompom.")
NEG = ("No text, no logo, no watermark, no cartoon outlines, no anime eyes, no visible "
       "sclera, no teeth, no plastic gloss, no 2D vector, no CGI Pixar look, no extra fingers.")
BASE = "TÉO stays on the left and plans; JUCA stays on the right and executes."


def acao(state, especifica, camera):
    return " ".join([STYLE, SET, state, JUCA, TEO, BASE, especifica,
                     "They do not speak and their mouths do not move.", camera, NEG])


CLIPES = [
    {"n": 5, "dur": 10, "estagio": "DIAGNOSTICO_ERRADO",
     "beats": ["TÉO monta um modelo de estante e põe toda a carga em miniatura no topo.",
               "O modelo inclina, mas TÉO usa uma vara para conferir apenas o espaço até o teto.",
               "JUCA instala a primeira travessa na posição máxima e ela continua subindo."],
     "action": acao(
        "State objects: four free-standing uprights occupy the first footprint; a tiny blank "
        "clay rack model rests on the back of TÉO's clipboard.",
        "TÉO places every miniature crate on the model's top shelf, leaving its lower level "
        "clear; the model leans while he checks only the roof clearance with a rod. JUCA copies "
        "the arrangement by lifting the first real crossbeam to its highest slots. The beam "
        "keeps rising between the uprights. Their eyes stay on the work.",
        "The camera makes one slow dolly from the model toward the real rack."),
     "overall_soundscape": "steel fasteners clink", "non_diegetic_music": "N/A"},
    {"n": 7, "dur": 10, "estagio": "PRIMEIRA_FALHA",
     "beats": ["TÉO mede a passagem livre ao lado da primeira prateleira.",
               "JUCA coloca uma única caixa pesada no alto e a chapa inteira se curva.",
               "JUCA ajeita a boina e retira o pallet jack enquanto a prateleira continua cedendo."],
     "action": acao(
        "State objects: one unanchored rack bay stands upright with a single high shelf; a "
        "heavy timber gearbox crate waits on the pallet jack.",
        "TÉO checks the generous empty aisle with a folding rule. JUCA raises the single crate "
        "onto the high shelf, making the whole sheet bow far more than the load suggests. He "
        "presses his cap into place and withdraws the pallet jack while the shelf keeps "
        "flexing. Their eyes stay on the work.",
        "The camera makes one slow dolly closer to the bowed shelf."),
     "overall_soundscape": "timber objects thud; loaded steel rack groans",
     "non_diegetic_music": "N/A"},
    {"n": 11, "dur": 10, "estagio": "JEITINHO",
     "beats": ["TÉO mede o menor caminho entre a estante e o pórtico transportador.",
               "JUCA prende uma cinta perfurada entre as duas estruturas e aperta a catraca.",
               "A estante para de oscilar, o pórtico inclina e um rolete continua girando."],
     "action": acao(
        "State objects: the top-heavy rack sways beside the upright conveyor gantry; a "
        "perforated steel strap lies ready between them.",
        "TÉO measures the shortest line from rack to gantry and gives a second restrained "
        "thumbs-up. JUCA ratchets the perforated strap between them. The rack stops swaying as "
        "the entire gantry leans toward it and one conveyor roller slowly turns. Their eyes "
        "stay on the work.",
        "The camera makes one slow dolly along the taut strap."),
     "overall_soundscape": "ratchet pawl clicks; loaded steel rack groans",
     "non_diegetic_music": "N/A"},
    {"n": 15, "dur": 10, "estagio": "PAUSA_COMICA",
     "beats": ["TÉO apoia o nível na prateleira arqueada durante a pausa.",
               "Um parafuso vibra para dentro da caneca de JUCA e a bolha fica centralizada por um instante.",
               "JUCA cobre a caneca com o pires enquanto a bandeja desliza e toda a estante oscila."],
     "action": acao(
        "State objects: the overloaded upper shelves sway above empty lower levels; a plain "
        "clay cup and saucer sit on a wheeled tray; one fastener trembles near the cup.",
        "TÉO rests the spirit level on the bowed shelf. The trembling fastener drops into "
        "JUCA's cup just as the level bubble centers. JUCA calmly covers the cup with its "
        "saucer while the wheeled tray glides and the entire rack sways behind it. Their eyes "
        "stay on the work.",
        "The camera makes one slow dolly toward the covered cup."),
     "overall_soundscape": "steel fasteners clink; loaded steel rack groans",
     "non_diegetic_music": "N/A"},
    {"n": 21, "dur": 10, "estagio": "CLIMAX",
     "beats": ["TÉO mede o deslocamento da base enquanto JUCA força o trilho direito com uma alavanca.",
               "O mesmo caminhão vermelho é expulso debaixo da estante e corre pela linha amarela.",
               "O brinquedo pressiona o destravamento do transportador e uma caixa industrial segue viajando nos roletes."],
     "action": acao(
        "State objects: the same red toy truck remains squeezed beneath the front-right base; "
        "an unmarked mechanical conveyor release treadle lies along its path; one crate rests "
        "on the idle rollers.",
        "TÉO gauges the creeping base while JUCA levers the right rail. The same toy truck "
        "shoots free, rolls along the yellow line and depresses the unmarked treadle. The "
        "conveyor begins carrying its industrial crate toward the rack. Their eyes stay on the "
        "work.",
        "The camera makes one slow lateral dolly following the toy truck."),
     "overall_soundscape": "steel fasteners clink; loaded steel rack groans",
     "non_diegetic_music": "N/A"},
    {"n": 25, "dur": 10, "estagio": "CLIMAX",
     "beats": ["O mesmo carimbo rola da maleta e pressiona a alavanca de descida do pallet jack.",
               "Todo o conjunto permanece suspenso durante 1,2 segundo de silêncio diegético.",
               "O apoio desce e as três estantes, as caixas e o pórtico tombam em cascata no espaço vazio.",
               "O carimbo e os últimos fragmentos continuam deslizando pelo primeiro plano."],
     "action": acao(
        "State objects: the same blank stamp rests at the lip of the open case; one pallet "
        "jack alone supports the leaning rack bank; the clear foreground lane contains TÉO "
        "left and JUCA right outside every fall path.",
        "The same stamp rolls down the tilted work surface and depresses the pallet jack "
        "release. All movement and diegetic sound hold for 1.2 seconds while TÉO retracts his "
        "tape and JUCA fits a cosmetic cap. The support lowers; all three racks, timber crates "
        "and the freestanding conveyor gantry topple through the empty work zone in a "
        "structural cascade. Only materials are damaged; both craftsmen remain untouched as "
        "the stamp and loose steel continue sliding. Their mild professional expressions "
        "remain unchanged and their eyes stay on the work.",
        "The camera makes one slow dolly backward with the widening collapse."),
     "overall_soundscape": ("rubber stamp thumps; 1.2-second diegetic silence; loaded steel "
                            "rack groans; steel assemblies crash"),
     "non_diegetic_music": "N/A"},
]

ep = {"titulo": "CARGA MÁXIMA",
      "logline": "TÉO e JUCA montam três estantes industriais para uma criança e corrigem a "
                 "sobrecarga até todo o conjunto tombar como uma entrega concluída.",
      "setor": "armazenagem industrial", "servico": "montagem", "cliente": "criança",
      "mecanismo": "sobrecarga cumulativa no topo de módulos sem ancoragem",
      "degrau_final": "D4 estrutural — tombamento integral das três estantes e do pórtico",
      "objetos_plantados": [
          {"objeto": "carimbo de latão com base de borracha sem letras", "plantado_no_clipe": 1, "pago_no_clipe": 25},
          {"objeto": "carretel industrial de madeira com cabo de aço", "plantado_no_clipe": 2, "pago_no_clipe": 23},
          {"objeto": "caminhão basculante vermelho de brinquedo", "plantado_no_clipe": 3, "pago_no_clipe": 21}],
      "callback_object": "carimbo de latão com base de borracha sem letras",
      "shots": CLIPES,
      "continuidade": ["TÉO à esquerda / JUCA à direita", "figurinos fixos",
                       "gelo — n/a: galpão seco", "pila de estantes crescendo por clipe",
                       "caminhão vermelho sob o trilho direito até o clipe 21"],
      "assinatura": "nota fiscal sem conteúdo legível emitida, carimbada e entregue em bandeja"}

pasta = F.EPISODIOS_DIR / SLUG
sdir = pasta / "settings"
sdir.mkdir(parents=True, exist_ok=True)
(pasta / "episodio.json").write_text(json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")

arquivos = []
for s in CLIPES:
    est = s["estagio"].lower()
    cfg = dict(F.TEMPLATE_SETTINGS)
    cfg["video_length"] = "10s"
    cfg["output_filename"] = f"{SLUG}_c{s['n']:02d}_{est}"
    cfg["prompt"] = F.prompt_dossie(s, ep)
    arq = sdir / f"{cfg['output_filename']}_settings.json"
    arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    arquivos.append(arq)
    print(f"settings: {arq.name} · prompt {len(cfg['prompt'])} chars", flush=True)

mp4s = []
for i, arq in enumerate(arquivos, 1):
    antes = time.time()
    print(f"\n[{i}/6] GERANDO {arq.stem} …", flush=True)
    r = subprocess.run([F.PYTHON_GEN, F.GEN_TEST, "--settings", str(arq), "--tag", f"{SLUG}_FUMACA_{i:02d}"],
                       cwd=str(F.DIR_GEN_TEST), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=7200)
    dur = time.time() - antes
    cand = []
    for raiz in (Path(F.DIR_GEN_TEST), Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")):
        cand += [p for p in glob.glob(str(raiz / "**" / "*.mp4"), recursive=True)
                 if os.path.getmtime(p) >= antes - 5]
    cand.sort(key=os.path.getmtime, reverse=True)
    mp4 = cand[0] if cand else None
    if mp4:
        mp4s.append(mp4)
    print(f"[{i}/6] {dur/60:.1f} min · rc={r.returncode} · mp4={Path(mp4).name if mp4 else 'NÃO ACHOU'}", flush=True)
    if r.returncode != 0:
        for ln in (r.stderr or "").strip().splitlines()[-14:]:
            print("   ", ln[:170], flush=True)
        if not mp4:
            print("FALHOU — abortando", flush=True)
            break

if len(mp4s) < 2:
    sys.exit(1)
lista = pasta / "fumaca_lista.txt"
with open(lista, "w", encoding="utf-8", newline="\n") as f:
    for m in mp4s:
        f.write(f"file '{m}'\n")
final = pasta / f"{SLUG}_fumaca_{len(mp4s)}clipes.mp4"
ff = subprocess.run([F.PYTHON_GEN, "-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True).stdout.strip()
subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(final)],
               capture_output=True, text=True)
print("\n=== FUMAÇA DE COMÉDIA CONCLUÍDA ===", flush=True)
print("final:", final, flush=True)
print(f"tamanho: {final.stat().st_size/1e6:.1f} MB" if final.exists() else "concat falhou", flush=True)
