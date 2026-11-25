# -*- coding: utf-8 -*-
"""cadeia_v8.py — FECHAMENTO DOS 60 s no MODO DE PRODUCAO 2 steps / 832x480.

Base: cadeia_v7.py (mesmo gate, mesmo scan_ceu, mesmos prompts/ancoras).
Diferencas:
  - MODO = 2 steps, 832x480, euler, guidance_phases=1 (receita medida no benchmark)
  - c01/c02 BANCADOS (20 s aprovado, 8/640) — nao re-renderiza; o montador reduz
    esses dois para 832x480 e junta com c03..c06 nativos
  - c03..c06 renderizados do zero em _v8 (sem fallback: se reprovar, a cadeia PARA
    e o clipe vira retake em 2/640, conforme decisao de producao)
  - frames/ancoras/relatorio/bank proprios (_v8) — nada do v7 e sobrescrito
Saida: cadeia_v8_relatorio.json + cadeia_v8_bancados.json
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


_log = open(EP / "cadeia_v8_run.log", "a", encoding="utf-8")
sys.stdout = _Tee(sys.stdout, _log)
sys.stderr = _Tee(sys.stderr, _log)
print("\n===== CADEIA V8 (2 steps / 832x480) · largada %s ====="
      % time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
import qc_visao, scan_ceu
KEY = qc_visao._chave()

# Receita validada no BENCHMARK_VELOCIDADE_2026-11-25.md (H3 2 steps + turbo LoRA).
MODO = {
    "num_inference_steps": 2,
    "resolution": "832x480",
    "sample_solver": "euler",
    "guidance_phases": 1,
}
ANCORA_INI = EP / "refs" / "ancora_v7_porta.png"
TENTATIVAS = 3
# (slug_base, tag, curto, cliente_autorizado, seed_base, tentativas)
# c01/c02 entram BANCADOS (skip). c03..c06 sao os clipes que faltam para os 60 s.
CLIPES = [
    ("operacao_ralo_exato_v4_c01_ligacao",          "V8_C01", "c01", True,  7017, 3),
    ("operacao_ralo_exato_v4_c02_cadeia",           "V8_C02", "c02", False, 7019, 3),
    ("operacao_ralo_exato_v4_c03_primeira_falha_v2","V8_C03", "c03", False, 7002, 3),
    ("operacao_ralo_exato_v4_c04_jeitinho_v6a",     "V8_C04", "c04", False, 7102, 3),
    ("operacao_ralo_exato_v4_c05_escalada_v6a",     "V8_C05", "c05", False, 7200, 3),
    ("operacao_ralo_exato_v4_c06_climax_v6a",       "V8_C06", "c06", True,  7200, 3),
]
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")
SET_NOVO = (
    "a small military vehicle-wash bay of riveted grey steel plates. Wet grey concrete "
    "floor, two faded yellow safety lines, one rectangular drain hole at centre with the grate "
    "lying face down beside it, red-wheel water valves and a coiled hose reel on the left wall, "
    "electric cabinets and a broom on the right wall, two stacked steel drums at rear right, "
    "ONE RIBBED STEEL ROLL-UP DOOR closed against the bay's rear steel wall, a bare chain "
    "with a hook above the drain, two caged industrial lamps hanging from the riveted steel "
    "ceiling. The interior of the bay fills the entire frame edge to edge: riveted steel "
    "walls and a riveted steel roof close the whole frame on every side and every top corner, "
    "so the view shows steel plates, caged lamps and the chain from floor to roof. "
    "Cool hard overhead light, short shadows, wet surfaces.")
PROPS = ("dark BAKELITE wall telephone box with handset and coiled cord (charcoal to dark green-grey - the shade the anchor photo establishes, and it NEVER changes within the episode) — EXACTLY ONE in the whole "
         "bay, fallen steel grate — EXACTLY ONE loose grate beside the centre drain. A grate "
         "lying in front of or touching the edge of the drain IS that same single loose "
         "grate (the drain partially behind it is never a second grate): there is never a "
         "second loose grate anywhere in the shot; the loose grate settles by the drain and "
         "stays there until the drum carries it in c02; never migrates on its own, steel "
         "drums standing at the rear (one drum is visible; no count is declared for "
         "background drums — only the ONE empty drum that rolls in c02 is counted); the "
         "steel drums carry a painted RING EMBLEM on their side — a decorative mark, NOT "
         "text, never flag it as texto_na_tela, rubber test plug, white absorbent pads that "
         "swell into one pillow, white "
         "paper sack, bucket cart with EXACTLY ONE galvanized metal bucket (never a second "
         "bucket), squeegee, pressure hose reel, red-wheel water valves, wall-mounted "
         "pressure gauges, electric cabinets with dials on the right wall, steel pipes along "
         "the walls, chain with hook, ribbed steel roll-up door at the back, red and yellow switch "
          "plates on the electric cabinets, broom, caged industrial lamps, "
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
        sufixo = "_v8" + ("" if tent == 0 else "_r%d" % tent)
        slug = slug_base + sufixo
        st = dict(st_base)
        st.update(MODO)
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
        print("\n=== %s · tentativa %d/%d · seed %d · %d steps %s · cliente=%s ==="
              % (slug, tent + 1, tent_max, st["seed"], MODO["num_inference_steps"],
                 MODO["resolution"], "SIM" if cliente else "NAO"), flush=True)
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
        f99 = EP / "refs" / ("ancora_v8_" + curto + ".png")
        f50 = EP / "refs" / ("meio_v8_" + curto + ".png")
        f02 = EP / "refs" / ("inicio_v8_" + curto + ".png")
        f20 = EP / "refs" / ("corte1_v8_" + curto + ".png")
        f30 = EP / "refs" / ("corte2_v8_" + curto + ".png")
        f08 = EP / "refs" / ("emenda_v8_" + curto + ".png")
        for ts, dst in (("9.9", f99), ("5.0", f50), ("3.0", f30), ("2.0", f20),
                        ("0.8", f08), ("0.2", f02)):
            subprocess.run([FF, "-y", "-ss", ts, "-i", str(mp4), "-frames:v", "1", str(dst)],
                           capture_output=True)
        ps = psnr_png(f02, ancora_png)
        print("  f0.2 vs ancora_in = %s dB (informativo)"
              % ("%.1f" % ps if ps is not None else "parse?"), flush=True)
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


if "--dry" in sys.argv:
    for slug_base, tag, curto, cliente, seed, _tt in CLIPES:
        sb = json.loads((SETDIR / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
        p = re.sub(r"AT START: (.+?)\. \[Shot", "AT START: <REALIDADE>. [Shot",
                   troca_set(sb["prompt"]), count=1, flags=16) + ALINHA
        low = p.lower()
        ok = ("ONE RIBBED STEEL ROLL-UP DOOR" in p and "no sky" not in low
              and "window" not in low and "wet surfaces." in p)
        print("%s: prompt ok=%s len=%d cliente=%s seed=%d"
              % (curto, ok, len(p), cliente, seed), flush=True)
    sys.exit(0)

if not ANCORA_INI.exists():
    raise SystemExit("XX ancora de abertura ausente: " + str(ANCORA_INI))


def salvar_relatorio():
    (EP / "cadeia_v8_relatorio.json").write_text(
        json.dumps(feitos, ensure_ascii=False, indent=2), encoding="utf-8")


BANK = EP / "cadeia_v8_bancados.json"
if BANK.exists():
    bancados = json.loads(BANK.read_text(encoding="utf-8"))
else:
    # Semeia o banco v8 com o 20 s JA APROVADO do v7 (c01+c02) — nao re-renderiza.
    v7 = json.loads((EP / "cadeia_v7_relatorio.json").read_text(encoding="utf-8"))
    bancados = {f["curto"]: f for f in v7
                if f.get("curto") in ("c01", "c02") and f.get("aprovado")}
    BANK.write_text(json.dumps(bancados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("banco v8 semeado com: %s" % ", ".join(sorted(bancados)), flush=True)

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
        # v8 de producao: SEM fallback. Se reprovar, para aqui e o clipe vira retake 2/640.
        print("XX %s nao aprovado — CADEIA V8 PARA (sem fallback)." % curto, flush=True)
        feitos.append({"slug": slug_base, "curto": curto, "estado_in_real": est_real,
                       "aprovado": False, "tentativas": tentativas})
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
print("\n>>> CADEIA V8: %d/%d clipes aprovados — relatorio: cadeia_v8_relatorio.json"
      % (n_ok, len(CLIPES)), flush=True)
if n_ok == len(CLIPES):
    print(">>> proximo passo: montar_final_v8.py", flush=True)
