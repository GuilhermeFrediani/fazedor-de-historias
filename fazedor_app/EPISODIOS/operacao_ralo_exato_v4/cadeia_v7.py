# -*- coding: utf-8 -*-
"""cadeia_v7.py — EPISODIO INTEIRO (c01..c06) com os consertos do dossie + auditoria 21/11:
  - ocupacao AGENDADA: cliente autorizado so no c01 (entrega) e c06 (fecho)
  - registro v2 (cor/posse/CONTAGEM) no PROPS e no gate — balde duplicado reprova
  - REDE DENSA DE CEU (scan_ceu) DENTRO do loop: reprova antes do gate semantico
  - gate em 5 frames (9.9 + 5.0 + 3.0 + 2.0 + 0.8 EMENDA) com estado real da ancora
  - enforcement completo no gate (ghost/extra/texto/flutuante/contagem) — nao so o prompt
  - 3 tentativas (seed+1), fallback controlado
Saida: cadeia_v7_relatorio.json
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


class _Tee:
    def __init__(self, *fs):
        self.fs = fs

    def __getattr__(self, name):
        # deixa passar reconfigure/isatty/encoding/fileno etc. para o stream real
        return getattr(self.fs[0], name)

    def write(self, s):
        for f in self.fs:
            try:
                f.write(s)
            except Exception:
                pass

    def flush(self):
        for f in self.fs:
            try:
                f.flush()
            except Exception:
                pass


# LOG EM ARQUIVO: sobrevive a reinicio do OpenCode (o .out da shell morre junto)
_log = open(EP / "cadeia_v7_run.log", "a", encoding="utf-8")
sys.stdout = _Tee(sys.stdout, _log)
sys.stderr = _Tee(sys.stderr, _log)
print("\n===== CADEIA V7 · largada %s =====" % time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
import qc_visao, scan_ceu
KEY = qc_visao._chave()

ANCORA_INI = EP / "refs" / "ancora_v7_abertura.png"
TENTATIVAS = 3
# (slug_base, tag, curto, cliente_autorizado, seed_base, tentativas)
# c01 ja queimou 3 tentativas (7001-7003) — recomeca em 7004 com 5 tentativas
# CONSERTO (auditoria 21/11): c01/c02 precisam ser RE-RENDERIZADOS (ghost de 1 s e
# balde duplicado passaram pelo banco). Seeds novas + moldes novos (planos[0] =
# ancora) = resultado novo mesmo com seed antiga. c03/c04 seguem bancados.
CLIPES = [
    ("operacao_ralo_exato_v4_c01_ligacao",          "V7_C01", "c01", True,  7012, 3),
    ("operacao_ralo_exato_v4_c02_cadeia",           "V7_C02", "c02", False, 7012, 3),
    ("operacao_ralo_exato_v4_c03_primeira_falha_v2","V7_C03", "c03", False, 7002, 3),
    ("operacao_ralo_exato_v4_c04_jeitinho_v6a",     "V7_C04", "c04", False, 7102, 3),
    ("operacao_ralo_exato_v4_c05_escalada_v6a",     "V7_C05", "c05", False, 7200, 3),
    ("operacao_ralo_exato_v4_c06_climax_v6a",       "V7_C06", "c06", True,  7200, 3),
]
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")
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
# CONSERTO 8 (auditoria 21/11): registro v2 sem CONTAGEM deixou o 2o balde de 15 s
# passar (nao era violacao de contrato). Agora toda grande peca declara QUANTAS
# unidades existem — e o gate (gate_ancora/SYS_A) reprova divergencia de contagem.
PROPS = ("white wall telephone box with handset and coiled cord — EXACTLY ONE in the whole "
         "bay, fallen steel grate — EXACTLY ONE loose grate beside the centre drain; the "
         "centre drain itself stays OPEN and uncovered and does NOT count as a grate; the "
         "loose grate settles in front of the drain and stays there until the drum carries "
         "it in c02; never migrates on its own, steel drums standing at the rear (one drum "
         "is visible; no count is declared for background drums — only the ONE empty drum "
         "that rolls in c02 is counted); the steel drums carry a painted RING EMBLEM on "
         "their side — a decorative mark, NOT text, never flag it as texto_na_tela, rubber "
         "test plug, white absorbent pads that swell into one pillow, white "
         "paper sack, bucket cart with EXACTLY ONE galvanized metal bucket (never a second "
         "bucket), squeegee, pressure hose reel, red-wheel water valves, wall-mounted "
         "pressure gauges, electric cabinets with dials on the right wall, steel pipes along "
         "the walls, chain with hook, white canvas curtain, broom, caged industrial lamps, "
         "wet concrete floor with yellow safety lines, folded metal ruler, "
         "brass tape hook (loose on the drain rim), "
         "steel tape measure (JUCA's chest pocket - never TEO's hand), "
         "YELLOW carpenter pencil (TEO's working pencil; pinned through the hook eye in c05; "
         "never red; JUCA's own small yellow pencil stays behind his right ear), "
         "green document case (inside the sealed drum in c06), "
         "BLANK white work-order sheet — EXACTLY ONE (no writing, no lines, no marks ever; client hands it to "
         "TEO in c01 and TEO keeps it in his chest pocket), "
         "phone box/base: intact until yanked off the wall in c01; any crack or dent only from a "
         "VISIBLE impact (the dolly caster in c02); never self-damages and never flickers between "
         "cracked and intact, "
         "steel grate: lies face down beside the drain until the drum carries it in c02; never "
         "migrates on its own, "
         "military client in olive uniform (clips 1 and 6 only, when announced by the estado)")


def troca_set(prompt):
    return re.sub(r"a small military vehicle-wash bay.*?wet surfaces\.", SET_NOVO,
                  prompt, flags=16)


def descrever_ancora(png):
    import base64
    SYS = ("Descreva este frame de claymation como um ESTADO DE CENA em UMA frase em "
           "ingles, objetiva: quem esta onde, o que cada um segura, que objetos existem "
           "e onde estao, estado do piso/agua. Sem interpretacao, so o que se ve. "
           'Responda JSON: {"estado": "uma frase EN"}')
    parts = [{"type": "image", "data": base64.b64encode(Path(png).read_bytes()).decode(),
              "mime_type": "image/png"}]
    tx = qc_visao._call(KEY, SYS, parts, max_tokens=2000)
    return json.loads(re.search(r"\{.*\}", tx, 16).group(0))["estado"]


def psnr_png(a, b):
    r = subprocess.run([FF, "-hide_banner", "-i", str(a), "-i", str(b),
                        "-filter_complex", "psnr", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"average:([0-9.]+|inf)", r.stderr)
    return 99.0 if (m and m.group(1) == "inf") else (float(m.group(1)) if m else None)


def _ok(j, ins=False):
    return (j.get("veredito") == "APROVADA"
            and not j.get("personagens_extras")
            and not j.get("objetos_flutuantes")
            and not j.get("fantasmas")
            and (j.get("dois_bonecos") is not False or ins))


def render_com_gate(slug_base, tag, curto, ancora_png, estado_real, cliente, seed_base, tent_max):
    st_base = json.loads((SETDIR / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
    mo_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", st_base["prompt"])
    estado_end = mo_end.group(1) if mo_end else ""
    tentativas = []
    for tent in range(tent_max):
        sufixo = "_v7" + ("" if tent == 0 else "_r%d" % tent)
        slug = slug_base + sufixo
        st = dict(st_base)
        st["output_filename"] = slug
        st["seed"] = seed_base + tent
        st["image_start"] = str(ancora_png)
        st["image_prompt_type"] = "S"
        p = troca_set(st_base["prompt"])
        st["prompt"] = (re.sub(r"AT START: (.+?)\. \[Shot",
                               "AT START: " + estado_real.replace("\\", "") + ". [Shot",
                               p, count=1, flags=16)
                        + ALINHA)
        sdf = SETDIR / (slug + "_settings.json")
        sdf.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n=== %s · tentativa %d/%d · seed %d · cliente=%s ==="
              % (slug, tent + 1, tent_max, st["seed"], "SIM" if cliente else "NAO"),
              flush=True)
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
        # --- REDE DENSA DE CEU (local, 0 GPU, 0 API) — antes de qualquer juiz ---
        sc = scan_ceu.escanear(mp4, passo=0.5, faixa=0.28, limiar=0.10)
        print("  SCAN CEU: %s%s" % (sc["veredito"], "" if not sc["violacoes"] else
              " " + "; ".join("%.1f-%.1fs pico %.0f%%" % (v["ini_s"], v["fim_s"], v["pico"] * 100)
                              for v in sc["violacoes"])), flush=True)
        if sc["violacoes"]:
            tentativas.append({"slug": slug, "seed": st["seed"], "rc": r.returncode,
                               "mp4": str(mp4), "scan_ceu": sc, "falha": "ceu"})
            print("  scan reprovou — retry seed+1", flush=True)
            continue
        f99 = EP / "refs" / ("ancora_v7_" + curto + ".png")
        f50 = EP / "refs" / ("meio_v7_" + curto + ".png")
        f02 = EP / "refs" / ("inicio_v7_" + curto + ".png")
        f20 = EP / "refs" / ("corte1_v7_" + curto + ".png")
        f30 = EP / "refs" / ("corte2_v7_" + curto + ".png")
        f08 = EP / "refs" / ("emenda_v7_" + curto + ".png")
        for ts, dst in (("9.9", f99), ("5.0", f50), ("3.0", f30), ("2.0", f20),
                        ("0.8", f08), ("0.2", f02)):
            subprocess.run([FF, "-y", "-ss", ts, "-i", str(mp4), "-frames:v", "1", str(dst)],
                           capture_output=True)
        ps = psnr_png(f02, ancora_png)
        print("  f0.2 vs ancora_in = %s dB (informativo)"
              % ("%.1f" % ps if ps is not None else "parse?"), flush=True)
        # gate em 5 frames: 9.9 (estado) + 5.0 + 3.0 + 2.0 + 0.8 (a EMENDA). O ghost de 1 s
        # do teste dos 20 s morava entre 0 e 2 s e nao era amostrado — 0.8 pega o morph
        # ancora->planos[0] exatamente onde ele nasce.
        planos = [("9.9", f99, estado_end, False), ("5.0", f50, "", False),
                  ("3.0", f30, "", True), ("2.0", f20, "", True), ("0.8", f08, "", True)]
        verds = {}
        for tg in range(15):
            try:
                verds = {}
                for ts, dst, est, ins in planos:
                    j = qc_visao.gate_ancora(KEY, str(dst), estado=est, props=PROPS,
                                             cliente=cliente, inserto=ins)
                    verds[ts] = j
                    print("  GATE f%s%s: %s - %s" % (ts, " (inserto)" if ins else "",
                                                    j.get("veredito"), j.get("motivo", "")),
                          flush=True)
                    print("    nao_plantados=%s props_violados=%s estado=%s cenario=%s fantasmas=%s"
                          % (j.get("objetos_nao_plantados"), j.get("props_violados"),
                             j.get("estado_divergente"), j.get("cenario_violado"),
                             j.get("fantasmas")), flush=True)
                break
            except BaseException as e:
                verds = {}
                print("  gate INDISPONIVEL (%s) - espero 120s e repito os MESMOS frames (%d/15)"
                      % (str(e)[:200], tg + 1), flush=True)
                time.sleep(120)
        if not verds:
            tentativas.append({"slug": slug, "seed": st["seed"], "rc": r.returncode,
                               "dur_min": round(dur, 1), "mp4": str(mp4), "psnr_f02": ps,
                               "scan_ceu": sc, "falha": "gate_indisponivel"})
            print("  gate indisponivel por 30 min - CADEIA PAUSADA (frames guardados; retome depois)",
                  flush=True)
            raise SystemExit(7)
        j99, j50 = verds["9.9"], verds["5.0"]
        tentativas.append({"slug": slug, "seed": st["seed"], "rc": r.returncode,
                           "dur_min": round(dur, 1), "mp4": str(mp4), "psnr_f02": ps,
                           "scan_ceu": sc, "gate_ancora": j99, "gate_meio": j50,
                           "gate_frames": dict(verds)})
        if all(_ok(verds[t], ins) for t, _d, _e, ins in planos):
            return mp4, f99, j99, j50, tentativas
        print("  gate reprovou - retry seed+1", flush=True)
    return None, None, None, None, tentativas


# FASE 1 (auditoria 21/11): --so20s re-renderiza SO os clipes 1-2 (a janela de
# aceite do usuario: 0 ghost, 0 duplicado, 0 texto, cliente, >=8/>=8). c03..c06
# ficam como estao (bancados/fallback) ate a fase do 60 s.
if "--so20s" in sys.argv:
    CLIPES = CLIPES[:2]

if "--dry" in sys.argv:
    for slug_base, tag, curto, cliente, seed, _tt in CLIPES:
        sb = json.loads((SETDIR / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
        p = re.sub(r"AT START: (.+?)\. \[Shot", "AT START: <REALIDADE>. [Shot",
                   troca_set(sb["prompt"]), count=1, flags=16) + ALINHA
        ok = ("fully ENCLOSED" in p) and ("no sky" in p) and ("no other people" in p) \
            and ("industrial lamps. Cool" not in p)
        print("%s: prompt ok=%s len=%d cliente=%s seed=%d"
              % (curto, ok, len(p), cliente, seed), flush=True)
    sys.exit(0)

if not ANCORA_INI.exists():
    raise SystemExit("XX ancora de abertura ausente: " + str(ANCORA_INI))

def salvar_relatorio():
    (EP / "cadeia_v7_relatorio.json").write_text(
        json.dumps(feitos, ensure_ascii=False, indent=2), encoding="utf-8")


BANK = EP / "cadeia_v7_bancados.json"
bancados = json.loads(BANK.read_text(encoding="utf-8")) if BANK.exists() else {}

ancora = ANCORA_INI
feitos = []
for slug_base, tag, curto, cliente, seed, tent_max in CLIPES:
    if curto in bancados:
        print("\n>>> %s BANCADO (gate ja resolvido) — pulando" % curto, flush=True)
        feitos.append(bancados[curto])
        ancora = Path(bancados[curto]["ancora_out"])
        salvar_relatorio()
        continue
    est_real = descrever_ancora(ancora)
    print("\n>>> estado REAL da ancora (%s): %s" % (curto, est_real), flush=True)
    mp4, f99, j99, j50, tentativas = render_com_gate(slug_base, tag, curto, ancora,
                                                     est_real, cliente, seed, tent_max)
    if not mp4:
        fb = EP / "refs" / ("ancora_v7_" + curto + ".png")
        mp_fb = next((t["mp4"] for t in reversed(tentativas) if t.get("mp4")), None)
        if fb.exists() and mp_fb:
            print("XX %s: tentativas reprovadas — CONTINUANDO com fallback controlado." % curto,
                  flush=True)
            feitos.append({"slug": slug_base, "curto": curto, "mp4": mp_fb,
                           "estado_in_real": est_real, "aprovado": False, "fallback": True,
                           "scan_ceu": tentativas[-1].get("scan_ceu"),
                           "gate_ancora": tentativas[-1].get("gate_ancora", {}),
                           "gate_meio": tentativas[-1].get("gate_meio", {}),
                           "ancora_out": str(fb), "tentativas": tentativas})
            ancora = fb
            salvar_relatorio()
            continue
        print("XX %s nao aprovado e sem fallback — cadeia para aqui." % slug_base, flush=True)
        feitos.append({"slug": slug_base, "estado_in_real": est_real,
                       "tentativas": tentativas, "aprovado": False})
        salvar_relatorio()
        break
    feitos.append({"slug": slug_base, "curto": curto, "mp4": str(mp4),
                   "estado_in_real": est_real, "aprovado": True,
                   "scan_ceu": tentativas[-1].get("scan_ceu"),
                   "gate_ancora": j99, "gate_meio": j50, "ancora_out": str(f99),
                   "gate_frames": tentativas[-1].get("gate_frames"),
                   "tentativas": tentativas})
    ancora = f99
    salvar_relatorio()

salvar_relatorio()
n_ok = sum(1 for f in feitos if f.get("aprovado"))
print("\n>>> CADEIA V7: %d/%d clipes aprovados — relatorio: cadeia_v7_relatorio.json"
      % (n_ok, len(CLIPES)), flush=True)
if n_ok + sum(1 for f in feitos if f.get("fallback")) == len(CLIPES):
    print(">>> proximo passo: montar_final_v7.py", flush=True)
