# -*- coding: utf-8 -*-
"""CADEIA PATCH v6a — re-render SOMENTE de c04/c05/c06 (a zona 30-60 s com todos
os defeitos do resumo do v5), partindo da ancora limpa do c03 (ancora_lha_v2,
sanity APROVADA no gate v3). c01-c03 do v5 ficam intactos e entram na emenda.

Mudancas vs cadeia_v2:
- GATE DUPLO por clipe: ancora f9.9 (estado AT END + props) E meio f5.0 (props).
  Ambos com veredito APROVADA obrigatorios (o v2 so olhava higiene da ancora).
- 3 tentativas (seed base+tent); 3a falha = cadeia para (regra da serie).
- Saidas novas _v6a (originais intocados); ancoras nomeadas explicitas
  ancora_v6a_cXX.png (sem a pegadinha do slug[-6:]).
- PSNR f0.2 vs image_start impresso (informativo).
Seeds 7100+ (o 7001 do v5 produziu os defeitos — sorteio novo).
"""
import json, re, subprocess, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
SETDIR = EP / "settings"
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao
KEY = qc_visao._chave()

ANCORA_INI = EP / "refs" / "ancora_lha_v2.png"   # c03 tail — sanity APROVADA (gate v3)
SEED_BASE = 7200   # rodada 3: sorteio novo (7100-7102 da rodada 1/2 ficam no historico)
TENTATIVAS = 3
CLIPES = [
    ("operacao_ralo_exato_v4_c04_jeitinho", "V6A_C04", "c04"),
    ("operacao_ralo_exato_v4_c05_escalada", "V6A_C05", "c05"),
    ("operacao_ralo_exato_v4_c06_climax",   "V6A_C06", "c06"),
]
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")

# LICOES DA RODADA 2 (renders bit-identicos, PSNR 0.1 dB iguais em 3/3):
# 1) o SET vive CONGELADO dentro do settings JSON — editar fumaca_v4.py (gerador)
#    nao muda renders existentes; a cirurgia tem que ser AQUI, no prompt, por render
# 2) negative_prompt e MORTO no H3 (handler: "no_negative_prompt": True) — o model
#    ignora por design; a unica alavanca de texto e o proprio prompt
# 3) mesma seed + mesmo prompt + mesma ancora = MESMO video (determinismo util:
#    aprova 1x e o clipe fica estável)
SET_NOVO = (
    "a small military vehicle-wash bay of riveted grey steel plates. Wet grey concrete "
    "floor, two faded yellow safety lines, one rectangular drain hole at centre with the grate "
    "lying face down beside it, red-wheel water valves and a coiled hose reel on the left wall, "
    "electric cabinets and a broom on the right wall, two stacked steel drums at rear right, a "
    "white canvas curtain on a ceiling rail at the back, a bare chain with a hook above the "
    "drain, two caged industrial lamps hanging from the riveted steel ceiling. The bay is "
    "fully ENCLOSED: the riveted steel ceiling spans the entire top of frame and solid steel "
    "walls close every side - no sky, no clouds, no windows, no daylight openings anywhere; "
    "when the camera looks up it sees only the steel ceiling, the caged lamps and the chain. "
    "Cool hard overhead light, short shadows, wet surfaces.")


def troca_set(prompt):
    """Substitui o paragrafo de set congelado (velho) pelo SET fechado anti-ceu.
    ATENCAO: nos settings congelados o set vive SEM prefixo 'SET:' (o enhancer o
    embutiu no bloco integrated_multimodal_description) — o alvo e o texto puro."""
    return re.sub(r"a small military vehicle-wash bay.*?wet surfaces\.", SET_NOVO,
                  prompt, flags=16)


PROPS = ("white wall telephone box with handset and coiled cord, fallen steel grate, steel "
         "drum, rubber test plug, absorbent pads / swollen pillow, white paper sack, bucket "
         "cart with plastic buckets, squeegee, floor-wash pedal, pressure hose reel, "
         "red-wheel water valves, wall-mounted pressure gauges, steel pipes along the walls, "
         "chain with hook, white canvas curtain, broom, tape measure, carpenter pencil, "
         "caged industrial lamps, wet concrete floor with yellow safety lines, folded metal "
         "ruler, military client in olive uniform ONLY when announced by the estado")


def descrever_ancora(png):
    """Gemini descreve o estado REAL da ancora (1 frase EN, objetos + posicoes)."""
    SYS = ("Descreva este frame de claymation como um ESTADO DE CENA em UMA frase em "
           "ingles, objetiva: quem esta onde, o que cada um segura, que objetos existem "
           "e onde estao, estado do piso/agua. Sem interpretacao, so o que se ve. "
           'Responda JSON: {"estado": "uma frase EN"}')
    import base64
    parts = [{"type": "image", "data": base64.b64encode(Path(png).read_bytes()).decode(),
              "mime_type": "image/png"}]
    tx = qc_visao._call(KEY, SYS, parts, max_tokens=2000)
    return json.loads(qc_visao._json_de(tx) and re.search(r"\{.*\}", tx, 16).group(0))["estado"]


def psnr_png(a, b):
    r = subprocess.run([FF, "-hide_banner", "-i", str(a), "-i", str(b),
                        "-filter_complex", "psnr", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"average:([0-9.]+|inf)", r.stderr)
    if not m:
        return None
    return float(m.group(1)) if m.group(1) != "inf" else 99.0


def _ok(j):
    """Gate individual: veredito + higiene."""
    return (j.get("veredito") == "APROVADA"
            and not j.get("personagens_extras")
            and not j.get("objetos_flutuantes")
            and j.get("dois_bonecos") is not False)


def render_com_gate(slug_base, tag, curto, ancora_png, estado_real):
    """Render + GATE DUPLO (ancora f9.9 + meio f5.0). Ate 3 tentativas, seed+1."""
    st_base = json.loads((SETDIR / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
    mo_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", st_base["prompt"])
    estado_end = mo_end.group(1) if mo_end else ""
    tentativas = []
    for tent in range(TENTATIVAS):
        sufixo = "_v6a" + ("" if tent == 0 else "_r%d" % tent)
        slug = slug_base + sufixo
        st = dict(st_base)
        st["output_filename"] = slug
        st["seed"] = SEED_BASE + tent
        st["image_start"] = str(ancora_png)
        st["image_prompt_type"] = "S"
        p = troca_set(st_base["prompt"])   # SET congelado e VELHO — troca por render
        st["prompt"] = (re.sub(r"AT START: (.+?)\. \[Shot",
                               "AT START: " + estado_real.replace("\\", "") + ". [Shot",
                               p, count=1, flags=16)
                        + ALINHA)
        sdf = SETDIR / (slug + "_settings.json")
        sdf.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n=== %s · tentativa %d/3 · seed %d ===" % (slug, tent + 1, st["seed"]), flush=True)
        t0 = time.time()
        r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", tag], cwd=CWD)
        dur = (time.time() - t0) / 60
        cand = [p for p in OUT.glob(slug + "*.mp4") if p.stat().st_mtime >= t0 - 5]
        print("  render rc=%d · %.1f min" % (r.returncode, dur), flush=True)
        if r.returncode != 0 or not cand:
            tentativas.append({"slug": slug, "seed": st["seed"], "rc": r.returncode,
                               "falha": "render"})
            continue
        mp4 = max(cand, key=lambda p: p.stat().st_mtime)
        # frames de prova
        f99 = EP / "refs" / ("ancora_v6a_" + curto + ".png")
        f50 = EP / "refs" / ("meio_v6a_" + curto + ".png")
        f02 = EP / "refs" / ("inicio_v6a_" + curto + ".png")
        for ts, dst in (("9.9", f99), ("5.0", f50), ("0.2", f02)):
            subprocess.run([FF, "-y", "-ss", ts, "-i", str(mp4), "-frames:v", "1", str(dst)],
                           capture_output=True)
        ps = psnr_png(f02, ancora_png)
        print("  f0.2 vs ancora_in = %s dB (informativo)"
              % ("%.1f" % ps if ps is not None else "parse?"), flush=True)
        # gate 4-frames de estado (informativo, como no v2)
        r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(OUT),
                            "--padrao", slug + "_*.mp4", "--settings", str(SETDIR),
                            "--saida", str(EP / ("qc_" + slug + ".json"))],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout[-400:], flush=True)
        # GATE DUPLO — o decisor
        j99 = qc_visao.gate_ancora(KEY, str(f99), estado=estado_end, props=PROPS)
        print("  GATE ANCOR f9.9: %s — %s" % (j99.get("veredito"), j99.get("motivo", "")), flush=True)
        print("    nao_plantados=%s cenario=%s" % (j99.get("objetos_nao_plantados"),
                                                   j99.get("cenario_violado")), flush=True)
        j50 = qc_visao.gate_ancora(KEY, str(f50), estado="", props=PROPS)
        print("  GATE MEIO  f5.0: %s — %s" % (j50.get("veredito"), j50.get("motivo", "")), flush=True)
        print("    nao_plantados=%s cenario=%s" % (j50.get("objetos_nao_plantados"),
                                                   j50.get("cenario_violado")), flush=True)
        tentativas.append({"slug": slug, "seed": st["seed"], "rc": r.returncode, "dur_min": round(dur, 1),
                           "psnr_f02": ps, "gate_ancora": j99, "gate_meio": j50})
        if _ok(j99) and _ok(j50):
            return mp4, f99, j99, j50, tentativas
        print("  gate reprovou — retry seed+1", flush=True)
    return None, None, None, None, tentativas


# RESUME: clipes ja APROVADOS em rodada anterior ficam bancados (a ancora de
# saida aprovada e o ponto de partida — nada de clipe aprovado re-renderiza)
rp = EP / "cadeia_patch_relatorio.json"
bancados = {}
if rp.exists():
    for f in json.loads(rp.read_text(encoding="utf-8")):
        if f.get("aprovado") and f.get("gate_ancora", {}).get("veredito") == "APROVADA" \
           and f.get("gate_meio", {}).get("veredito") == "APROVADA":
            bancados[f["curto"]] = f

# DRY: valida a cirurgia de SET em TODOS os prompts sem queimar 1 segundo de GPU
if "--dry" in sys.argv:
    for slug_base, tag, curto in CLIPES:
        sb = json.loads((SETDIR / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
        p = re.sub(r"AT START: (.+?)\. \[Shot", "AT START: <REALIDADE>. [Shot",
                   troca_set(sb["prompt"]), count=1, flags=16) + ALINHA
        ok = ("fully ENCLOSED" in p) and ("no sky" in p) and ("looks up" in p) \
            and ("hanging from the riveted steel ceiling" in p) \
            and ("industrial lamps. Cool" not in p)
        print("%s: prompt ok=%s len=%d ocorrencias_do_set=%d"
              % (curto, ok, len(p), p.count("vehicle-wash bay")), flush=True)
        if curto == "c05":
            print("---- c05 (primeiros 1000 chars) ----")
            print(p[:1000], flush=True)
    sys.exit(0)

ancora = ANCORA_INI
feitos = []
for slug_base, tag, curto in CLIPES:
    if curto in bancados:
        print("\n>>> %s BANCADO da rodada anterior (gate duplo aprovado) — pulando" % curto,
              flush=True)
        feitos.append(bancados[curto])
        ancora = Path(bancados[curto]["ancora_out"])
        continue
    est_real = descrever_ancora(ancora)
    print("\n>>> estado REAL da ancora: %s" % est_real, flush=True)
    mp4, f99, j99, j50, tentativas = render_com_gate(slug_base, tag, curto, ancora, est_real)
    if not mp4:
        print("XX %s nao aprovado em 3 tentativas — cadeia para aqui (regra da serie)."
              % slug_base, flush=True)
        feitos.append({"slug": slug_base, "estado_in_real": est_real,
                       "tentativas": tentativas, "aprovado": False})
        break
    feitos.append({"slug": slug_base, "curto": curto, "mp4": str(mp4),
                   "estado_in_real": est_real, "aprovado": True,
                   "gate_ancora": j99, "gate_meio": j50, "ancora_out": str(f99),
                   "tentativas": tentativas})
    ancora = f99  # a realidade avanca so com gate aprovado

(EP / "cadeia_patch_relatorio.json").write_text(
    json.dumps(feitos, ensure_ascii=False, indent=2), encoding="utf-8")
n_ok = sum(1 for f in feitos if f.get("aprovado"))
print("\n>>> CADEIA PATCH: %d/3 clipes aprovados — relatorio: cadeia_patch_relatorio.json"
      % n_ok, flush=True)
if n_ok == 3:
    print(">>> proximo passo: montar_final_v6a.py (emenda com c01-c03 do v5)", flush=True)
