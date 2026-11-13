# -*- coding: utf-8 -*-
"""
FUMAÇA v3 — 6 clipes CONSECUTIVOS de "OPERAÇÃO RALO EXATO".

Diferença crítica em relação à fumaça anterior: aqui os clipes #1..#6 são
adjacentes (a mesma obra, o mesmo minuto), não um salto #1 → #10 → #15 → #21.
É isso que permite testar continuidade de estado, que era o furo escondido.

Uso:  python fumaca_v3.py            (gera + concatena)
      python fumaca_v3.py --seco     (só valida e escreve os settings, sem render)
"""
import json, os, subprocess, sys, time, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
import fazedor_app as F

SLUG = "operacao_ralo_exato_v3"

SET_LAVADOR = (
    "SET: interior of a small military vehicle-wash bay built from riveted grey steel plates. "
    "Grey painted concrete floor with two faded yellow safety lines, one rectangular steel floor "
    "drain with long slots in the centre, red-wheel water valves and a coiled hose reel on the "
    "left wall, electric cabinets and a broom on the right wall, two stacked steel drums at the "
    "rear right, a white canvas containment curtain on a ceiling rail across the back, "
    "a bare hanging chain with a hook above the drain and two caged industrial lamps on the "
    "ceiling. Cool hard overhead light, soft short shadows, everything wet and soapy."
)

CLIPES = [
    {"n": 1, "dur": 10, "estagio": "LIGACAO",
     "estado_in": "TEO ao telefone de parede; carrinho de baldes ao lado de JUCA; piso seco.",
     "estado_out": "Telefone arrancado da parede, fone no chão; carrinho virado para a saída.",
     "beats": ["TEO estica o fio espiral para alcançar a trena e o fio engancha na alça do carrinho.",
               "JUCA puxa esse carrinho para o outro lado sem olhar.",
               "O fio estica e arranca o telefone da parede; o fone bate no concreto."],
     "gag": "o fio esticado entre os dois arranca o telefone da parede - e o carrinho nem sai do lugar.",
     "objeto_gag": "fio espiral do telefone",
     "fisica": "quicar",
     "reacao": "os dois olham o fone no chão, depois um para o outro; JUCA ajeita a boina com um resfôlego.",
     "action": ("TEO's handset cord snags the cart handle as he reaches for his tape measure. JUCA yanks that cart away without looking, and the cord rips the wall telephone off its plate. The receiver swings on the cord and clacks on the concrete. Both look down at it, then at each other."),
     "camera": "Static medium two-shot at puppet eye level, the action flowing continuously.",
     "overall_soundscape": ("bakelite receiver rattles on steel; cord twangs; phone plate clangs on "
                            "concrete; short snort")},
    {"n": 2, "dur": 10, "estagio": "CHEGADA",
     "estado_in": "Telefone no chão; entra o cliente militar pela cortina.",
     "estado_out": "Tambor de aço solto rolando pelo box; cliente já saiu.",
     "beats": ["O cliente bate no pulso e aponta o ralo; TEO abre a trena.",
               "JUCA empurra o carrinho do tambor na direção do ralo.",
               "Uma rodinha sobe no fone caído e o tambor vazio rola para fora do carrinho."],
     "gag": "a rodinha sobe no fone e o tambor desce sozinho do carrinho, rolando pelo box.",
     "objeto_gag": "tambor de aço vazio",
     "fisica": "rolar",
     "reacao": "JUCA coça a nuca; TEO levanta um dedo como quem ia avisar; suspiro curto.",
     "action": ('JUCA rolls the low drum dolly toward the drain and its caster climbs onto the fallen receiver. TEO points at the dolly one beat too late. The dolly tips and the empty steel drum rolls off across the wet bay. JUCA scratches his neck while TEO lifts one finger.'),
     "camera": "Static wide two-shot, the drum crossing frame, the action flowing continuously.",
     "overall_soundscape": ("boot heels on steel plate; caster scrapes over bakelite; hollow steel "
                            "drum rolls on concrete; short sigh")},
    {"n": 3, "dur": 10, "estagio": "PRIMEIRA_FALHA",
     "estado_in": "Tambor rolando; ralo livre; TEO com a trena aberta.",
     "estado_out": "Grelha do ralo virada de cabeça para baixo no piso; tampão de teste entalado.",
     "beats": ["TEO mede o vão do ralo e mostra a medida com dois dedos.",
               "JUCA encaixa um tampão de borracha grande no bocal com o calcanhar.",
               "O tampão incha e levanta a grelha de aço, que gira e cai virada no piso."],
     "gag": "o tampão incha mais que o bocal e a grelha de aço salta do chão como uma tampa.",
     "objeto_gag": "grelha de aço do ralo",
     "fisica": "tombar",
     "reacao": "TEO bate o lápis no queixo e aponta a grelha virada; JUCA assente devagar.",
     "action": ('TEO measures the drain opening and holds two fingers up as the accepted span. JUCA wedges an oversized rubber test plug into the throat with his heel. The rubber swells past the rim and lifts the steel grate, which flips over and lands face down. TEO taps his pencil on his chin and JUCA nods slowly.'),
     "camera": "Static medium shot centred on the drain, the action flowing continuously.",
     "overall_soundscape": ("brass tape clicks over steel; rubber squeaks against steel; steel grate "
                            "rings on concrete; low huff")},
    {"n": 4, "dur": 10, "estagio": "JEITINHO",
     "estado_in": "Grelha virada no piso, ralo entupido, piso ainda seco.",
     "estado_out": "Piso molhado, mantas encharcadas empilhadas sobre o ralo.",
     "beats": ["JUCA pisa no pedal de lavagem para provar que a linha funciona.",
               "A água jorra pelos bocais baixos e levanta as mantas absorventes soltas.",
               "As mantas inchadas de água deslizam e caem em pilha em cima do ralo."],
     "gag": "as mantas bebem a água, incham e desabam exatamente em cima do ralo que já estava entupido.",
     "objeto_gag": "mantas absorventes",
     "fisica": "transbordar",
     "reacao": "TEO ergue a trena para não molhar; JUCA olha a pilha e limpa a mão na calça; resfôlego.",
     "action": ('JUCA stamps the floor-wash pedal and water bursts from the low outlets along the floor. TEO lifts his tape clear of the spray. The loose absorbent pads soak it up, swell and slide together into a heap directly over the blocked drain. JUCA wipes one hand on his trousers.'),
     "camera": "Static low-angle two-shot at floor height, the action flowing continuously.",
     "overall_soundscape": ("steel pedal clanks; water bursts on concrete; soaked pads slap the floor; "
                           "wet huff")},
    {"n": 5, "dur": 10, "estagio": "ESCALADA",
     "estado_in": "Ralo coberto por mantas encharcadas; tampão ainda entalado; piso alagado.",
     "estado_out": "Tampão inflado fora do ralo, grelha em pé; TEO com a bota molhada.",
     "beats": ["JUCA conecta o engate de ar no tampão sem conferir a pressão.",
               "O tampão infla embaixo da grelha e levanta tudo como uma tampa.",
               "TEO apoia as duas mãos na grelha para segurar e sobe junto com ela."],
     "gag": "o tampão infla e a grelha sobe com o TEO pendurado nela, sem parar de subir.",
     "objeto_gag": "tampão pneumático",
     "fisica": "inflar",
     "reacao": "TEO olha a própria bota no ar; JUCA ajeita a boina; os dois soltam um resfôlego.",
     "action": ('JUCA snaps the air coupler onto the trapped plug and the rubber swells under the steel grate. TEO presses both hands on the plate to hold it down. The plate rises anyway and lifts TEO with it, his boots leaving the wet floor. JUCA fits his cap back into place.'),
     "camera": "Static medium two-shot, the rise kept in frame, the action flowing continuously.",
     "overall_soundscape": ("air coupler clicks; compressed air hisses through rubber; steel plate "
                            "scrapes upward; surprised snort")},
    {"n": 6, "dur": 10, "estagio": "CLIMAX",
     "estado_in": "Grelha em pé sobre o tampão inflado; piso alagado; cliente na cortina.",
     "estado_out": "Ralo fechado pela grelha, água cobrindo as botas, nota entregue na pasta.",
     "beats": ["TEO desce e pisa no tampão com as duas botas para forçá-lo de volta.",
               "O tampão escapa de lado e a grelha bate no chão cobrindo o ralo vazio.",
               "A água sobe pelas botas dos dois enquanto o cliente abre a pasta na cortina."],
     "gag": "o tampão escapa de lado e a grelha desliza para baixo, fechando o ralo vazio com um estalo.",
     "objeto_gag": "grelha de aço",
     "fisica": "escorregar",
     "reacao": "TEO e JUCA olham as próprias botas dentro da água; o cliente fecha a pasta e sai.",
     "action": ('TEO plants both boots on the swollen plug and it slips out sideways. JUCA pushes the standing water with one squeegee. The steel grate slaps down over the empty drain and water rises over both pairs of boots. At the curtain the military client closes his case and steps out.'),
     "camera": "Static wide two-shot including the curtain, the action flowing continuously.",
     "overall_soundscape": ("boots press wet rubber; rubber slips out with a pop; steel grate claps on "
                            "concrete; water laps at boots; long sigh")},
]

EP = {
    "titulo": "OPERAÇÃO RALO EXATO (v3)",
    "logline": ("TEO mede o ralo com precisão e JUCA o sela com o tampão errado; a água volta, o piso "
                "alaga e a dupla entrega o serviço mesmo assim."),
    "setor": "depósito militar de manutenção industrial",
    "servico": "lavagem pressurizada do box antes de uma inspeção",
    "cliente": "encarregado militar mudo",
    "mecanismo": ("o tampão pneumático de teste, semelhante a uma cabeça de limpeza, veda o ralo em vez "
                  "de limpá-lo, e toda a água de lavagem volta para o piso"),
    "degrau_final": "piso: a água retorna e cobre o box",
    "objetos_plantados": [
        {"objeto": "fio espiral do telefone", "plantado_no_clipe": 1, "pago_no_clipe": 2}],
    "callback_object": "fio espiral do telefone",
    "set_historia": SET_LAVADOR,
    "continuidade": [
        "TEO à esquerda com a trena; JUCA à direita executando",
        "figurinos fixos, mesma luz dura de cima",
        "o telefone fica no chão do clipe 1 ao 2 e não volta à parede",
        "o ralo é selado no clipe 3 e continua selado até o 6",
        "a água cresce a cada clipe: seco (1) -> molhado (4) -> alagado (6)"],
    "assinatura": ("nota fiscal sem escrita legível sai da pasta aberta do cliente, que fecha a pasta "
                   "e sai pela cortina"),
    "shots": CLIPES,
}

pasta = F.EPISODIOS_DIR / SLUG
sdir = pasta / "settings"
sdir.mkdir(parents=True, exist_ok=True)
(pasta / "episodio.json").write_text(json.dumps(EP, ensure_ascii=False, indent=2), encoding="utf-8")

# ── validação (é AQUI que se vê se o episódio é filmável) ─────────────────
r = F.validar_dossie(EP)
print("=" * 78)
print("VALIDAÇÃO v3 —", EP["titulo"])
print("=" * 78)
print("NOTA FINAL: %s/10  (humor %s · render %s)" % (r.get("nota"), r.get("humor"), r.get("render")))
for c in r.get("checks_render", []):
    print("  ok -", c)
for w in r.get("avisos", []):
    print("  AVISO ", w)
for e in r.get("erros", []):
    print("  ERRO  ", e)
print("=" * 78)
if r.get("erros"):
    print("%d erro(s) — o render seria desperdício de GPU. Corrija antes." % len(r["erros"]))
    if "--seco" not in sys.argv:
        sys.exit(1)

# ── settings ──────────────────────────────────────────────────────────────
arquivos = []
for s in CLIPES:
    cfg = dict(F.TEMPLATE_SETTINGS)
    cfg["video_length"] = "10s"
    cfg["output_filename"] = f"{SLUG}_c{s['n']:02d}_{s['estagio'].lower()}"
    cfg["prompt"] = F.prompt_dossie(s, EP)
    arq = sdir / f"{cfg['output_filename']}_settings.json"
    arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    arquivos.append(arq)
    print(f"settings: {arq.name} · prompt {len(cfg['prompt'])} chars · action "
          f"{len(s['action'].split())} palavras")

if "--seco" in sys.argv:
    print("\n--seco: settings escritos, nenhum render disparado.")
    sys.exit(0)

# ── render ────────────────────────────────────────────────────────────────
mp4s = []
for i, arq in enumerate(arquivos, 1):
    t0 = time.time()
    print(f"\n[{i}/6] GERANDO {arq.stem} …", flush=True)
    r = subprocess.run([F.PYTHON_GEN, F.GEN_TEST, "--settings", str(arq),
                        "--tag", f"{SLUG}_FUMACA_{i:02d}"],
                       cwd=str(F.DIR_GEN_TEST), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=7200)
    dur = time.time() - t0
    cand = []
    for raiz in (Path(F.DIR_GEN_TEST), Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")):
        cand += [p for p in glob.glob(str(raiz / "**" / "*.mp4"), recursive=True)
                 if os.path.getmtime(p) >= t0 - 5]
    cand.sort(key=os.path.getmtime, reverse=True)
    mp4 = cand[0] if cand else None
    if mp4:
        mp4s.append(mp4)
    print(f"[{i}/6] {dur/60:.1f} min · rc={r.returncode} · mp4={Path(mp4).name if mp4 else 'NÃO ACHOU'}",
          flush=True)
    if r.returncode != 0:
        for ln in (r.stderr or "").strip().splitlines()[-12:]:
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
print("\n=== FUMAÇA v3 CONCLUÍDA ===", flush=True)
print("final:", final, flush=True)
print(f"tamanho: {final.stat().st_size/1e6:.1f} MB" if final.exists() else "concat falhou", flush=True)
