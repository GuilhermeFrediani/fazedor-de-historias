# -*- coding: utf-8 -*-
"""FUMAÇA MANUAL — reconstrói os 3 primeiros clipes do episódio gerado no navegador
(transcrição fiel do usuário) e roda o gen_test em sequência + concatena."""
import json, io, os, subprocess, sys, time, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
import fazedor_app as F

SLUG = "gelo_no_atrio"
STYLE = ("Claymation plasticine stop-motion style. Handcrafted modelling clay puppets with "
         "visible fingerprints, tool marks and thumb-pressed texture, matte with gentle satin "
         "sheen, photographed on a miniature practical set. Visual artefacts: subtle "
         "frame-by-frame registration shifts and tiny practical-set seams.")
SET_OFICINA = ("SET: interior of a small 1970s Czech suburban workshop. Cream stucco wall with "
               "damp stains, sloped ceiling with reddish exposed wooden beams, moss-green "
               "wooden casement window with white lace curtain on the left, worn wooden "
               "workbench on the right with an iron vise, hammer and loose nails, pegboard with "
               "hanging wrenches and pliers, wooden ladder leaning on the back wall, wooden "
               "floorboards with sawdust, tilted wooden crate, galvanised bucket, open paint "
               "tin, red watering can in the background. Soft diffuse overcast daylight through "
               "the window, warm colour temperature, soft short shadows.")
SET_ATRIO = ("SET: a 1970s Central European hospital atrium, pale mint ceramic wall tiles, "
             "cream terrazzo floor, frosted-glass swing door at rear, chrome wall rails, an "
             "empty stainless trolley bay, exposed copper service pipes, suspended white "
             "acoustic ceiling grid, and diffuse overcast daylight from high windows; soft "
             "short shadows, warm-neutral colour.")
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


def acao(set_, state, especifica, camera):
    return " ".join([STYLE, set_, state, JUCA, TEO, especifica,
                     "They do not speak and their mouths do not move.", camera, NEG])


CLIPES = [
    {"n": 1, "dur": 10, "estagio": "LIGACAO",
     "beats": ["Phone bell vibrates", "TÉO checks a shape-only plan",
               "JUCA packs the planted brass stamp", "Crate rolls toward the exit"],
     "action": acao(SET_OFICINA,
        "STATE: A brass mechanical invoice stamp with a geometric die sits visibly in an open "
        "green toolbox; a translucent shape-only assembly plan lies beside a cream rotary "
        "telephone; a colour-tabbed flatpack crate waits by the door.",
        "TÉO remains on the left, lifts the vibrating receiver, studies the shape-only plan "
        "through a folding rule, then returns the receiver without vocalizing. JUCA remains on "
        "the right, nests the planted brass stamp in the toolbox, closes its latch, and pushes "
        "the flatpack crate toward the doorway, with both crate wheels still turning.",
        "The camera makes one slow dolly toward the rolling crate."),
     "overall_soundscape": "brass phone bells rattle; paper sheets rustle; steel latches click",
     "non_diegetic_music": "N/A"},
    {"n": 2, "dur": 10, "estagio": "CHEGADA",
     "beats": ["Groom points to his watch", "Groom indicates the empty cake plinth",
               "TÉO opens the plan while JUCA steadies the crate", "Groom strides away"],
     "action": acao(SET_ATRIO,
        "STATE: The colour-tabbed flatpack crate rests beside an empty round cake plinth; the "
        "planted chrome privacy screen has an opaque pale-blue curtain and one turned caster.",
        "TÉO occupies the left and unrolls the geometric plan; JUCA occupies the right and "
        "steadies the crate. At centre, a mute groom puppet in a cream suit, black bow tie and "
        "white clay boutonniere, with black-dot eyes without sclera and a closed line mouth "
        "with no teeth, points rapidly between a numeral-free wristwatch and the empty plinth, "
        "circles one forearm briskly, then strides through the rear door while the planted "
        "screen caster slowly swivels.",
        "The camera makes one slow lateral track from left to right."),
     "overall_soundscape": "wooden clogs knock on tile; paper sheets rustle; steel latches click",
     "non_diegetic_music": "N/A"},
    {"n": 3, "dur": 10, "estagio": "CHEGADA",
     "beats": ["TÉO gauges the doorway", "JUCA seats the planted red wedge",
               "JUCA guides the crate", "Crate wheels continue turning"],
     "action": acao(SET_ATRIO,
        "STATE: The privacy screen is parked beside the trolley bay; a loose red rubber door "
        "wedge lies under the rear swing door; the flatpack crate approaches the doorway.",
        "TÉO stays on the left and stretches his yellow tape across the doorway while marking "
        "clearance with geometric tokens. JUCA stays on the right, presses the planted red "
        "wedge firmly beneath the door with one clog, grips the large crate rather than passing "
        "any small object, and guides it through as its wheels continue rotating.",
        "The camera makes one slow backward dolly ahead of the crate."),
     "overall_soundscape": "wooden clogs knock on tile; steel latches click; plastic modules clack",
     "non_diegetic_music": "N/A"},
]

ep = {"titulo": "GELO NO ATRIO",
      "logline": "TÉO e JUCA montam um expositor refrigerado de casamento num átrio hospitalar, "
                 "mas a sequência invertida volta o evaporador para fora e congela a estrutura.",
      "setor": "hospitalar", "servico": "montagem", "cliente": "noivo",
      "mecanismo": "inverteu a ordem",
      "degrau_final": "estrutural — grelha suspensa do teto deslocada e arqueada pelo gelo",
      "objetos_plantados": [
          {"objeto": "carimbo mecânico de latão com selo geométrico", "plantado_no_clipe": 1, "pago_no_clipe": 25},
          {"objeto": "biombo cromado sobre rodízios com cortina azul", "plantado_no_clipe": 2, "pago_no_clipe": 23},
          {"objeto": "cunha vermelha de borracha", "plantado_no_clipe": 3, "pago_no_clipe": 21}],
      "callback_object": "carimbo mecânico de latão com selo geométrico",
      "shots": CLIPES,
      "continuidade": ["TÉO à esquerda / JUCA à direita em todos os clipes",
                       "figurinos fixos dos dois personagens",
                       "luz difusa de vitrós altos",
                       "gelo acumulando progressivamente nos objetos",
                       "cunha sob a porta até o clímax"],
      "assinatura": "nota fiscal emitida com selo geométrico e entregue ao cliente mudo"}

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
    arquivos.append((arq, s["n"], est))
    print(f"settings: {arq.name} · prompt {len(cfg['prompt'])} chars", flush=True)

mp4s = []
for i, (arq, n, est) in enumerate(arquivos, 1):
    tag = f"{SLUG}_FUMACA_{i:02d}"
    antes = time.time()
    print(f"\n[{i}/3] GERANDO {arq.stem} …", flush=True)
    r = subprocess.run([F.PYTHON_GEN, F.GEN_TEST, "--settings", str(arq), "--tag", tag],
                       cwd=str(F.DIR_GEN_TEST), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=7200)
    dur = time.time() - antes
    cand = [p for p in glob.glob(str(Path(F.DIR_GEN_TEST) / "**" / "*.mp4"), recursive=True)
            if os.path.getmtime(p) >= antes - 5]
    cand.sort(key=os.path.getmtime, reverse=True)
    mp4 = cand[0] if cand else None
    if mp4:
        mp4s.append(mp4)
    print(f"[{i}/3] {dur/60:.1f} min · rc={r.returncode} · mp4={Path(mp4).name if mp4 else 'NÃO ACHOU'}", flush=True)
    if r.returncode != 0:
        for ln in (r.stderr or "").strip().splitlines()[-14:]:
            print("   ", ln[:170], flush=True)
        if not mp4:
            print("FALHOU — abortando", flush=True)
            break

if not mp4s:
    sys.exit(1)
lista = pasta / "fumaca_lista.txt"
lista.write_text("\n".join(f"file '{m}'" for m in mp4s), encoding="utf-8")
final = pasta / f"{SLUG}_fumaca_{len(mp4s)}clipes.mp4"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                "-c", "copy", str(final)], capture_output=True, text=True)
print("\n=== FUMAÇA CONCLUÍDA ===", flush=True)
print("final:", final, flush=True)
print(f"tamanho: {final.stat().st_size/1e6:.1f} MB" if final.exists() else "concat falhou", flush=True)
