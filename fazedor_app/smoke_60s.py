# -*- coding: utf-8 -*-
"""smoke_60s.py — FUMACA de 1 minuto do episodio gerado pelo MOTOR (autoepisodio).

Le EPISODIOS/_smoke_meta.json (gravado pelo teste_autoepisodio_60s.py) e roda o
pipeline inteiro do episodio novo, com as lições da cadeia v7:
  FASE 0: ancora de abertura (draft 5 s -> frame 4.4 -> gate de visao) [3 tentativas]
  FASE 1: cadeia c01..cN (render -> scan_ceu -> gate 5 frames -> banco)
          - SET 100% do episodio (prompt do app); AT START trocado pelo estado REAL
            da ancora (descrição da visão) + linha de referencia da <Picture 1>;
          - gate em 9.9/5.0/3.0/2.0/0.8 s; cliente autorizado so nos clipes 1 e N;
          - 3 tentativas (seed+1), fallback controlado, banco (skip do que passou).
  FASE 2: montagem final (stage c01..cN + pos_producao --cortar-meio) + qc episodico.

Uso:
  python smoke_60s.py           # tudo (ancora + cadeia + final)
  python smoke_60s.py --dry     # so mostra os prompts montados (0 GPU)
Log: <pasta>/smoke_run.log  ·  relatorio: <pasta>/smoke_relatorio.json
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
APP = Path(__file__).resolve().parent
EPISODIOS = APP / "EPISODIOS"
META = EPISODIOS / "_smoke_meta.json"
PIPE = APP.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao, scan_ceu  # noqa: E402  (visao + varredura de ceu; escopo do MODULO)
TENT_MAX = 3
TENT_ANCORA = 5                        # a ancora e a fundacao: 5 tentativas
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")


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


def carregar():
    if not META.exists():
        raise SystemExit("XX meta ausente (%s) — rode teste_autoepisodio_60s.py antes." % META)
    m = json.loads(META.read_text(encoding="utf-8"))
    ep = Path(m.get("pasta") or (EPISODIOS / m["slug"]))
    e = json.loads((ep / "episodio.json").read_text(encoding="utf-8"))
    return m, ep, e


def settings_clipes(slug, setdir, e):
    """Os settings base dos clipes (c01..cN), na ordem — pelo nome EXATO que o
    gerar_settings usa (as tentativas da propria cadeia gravam _sm/_rX e NAO entram)."""
    arqs = []
    for s in (e.get("shots") or []):
        mo = re.search(r"\d+", str(s.get("n", 0)))
        n = int(mo.group()) if mo else 0
        est = re.sub(r"[^a-z0-9]+", "-", str(s.get("estagio", "plano")).lower()).strip("-")
        f = setdir / ("%s_c%02d_%s_settings.json" % (slug, n, est))
        if not f.exists():
            raise SystemExit("XX settings ausente: " + str(f))
        arqs.append(f)
    return arqs


def props_do_episodio(e):
    partes = []
    for o in e.get("objetos_plantados") or []:
        partes.append(
            "%s — EXACTLY ONE; planted in clip %s, pays off in clip %s; never duplicated, "
            "never teleports and never disappears without a VISIBLE action"
            % (o.get("objeto"), o.get("plantado_no_clipe"), o.get("pago_no_clipe")))
    if e.get("callback_object"):
        partes.append("the callback object %s returns in the final clip (payoff)"
                      % e.get("callback_object"))
    partes.append("the BLANK work-order sheet stays perfectly blank (no writing, no lines, "
                  "no marks of any kind at any moment)")
    set_his = str(e.get("set_historia", "") or "").strip()
    if set_his:
        partes.append("BACKGROUND FIXTURES of the set, declared by the episode and never "
                      "becoming gags, never moving on their own and never duplicating: "
                      + set_his)
    partes.append("plain small background containers, cloths and tools (bucket, cloth, broom, "
                  "papers on a bench) never register as unplanted - only the registry objects "
                  "and big furniture count")
    partes.append("puppet-attached props are part of the puppets and are never unplanted: the "
                  "YELLOW pencil behind JUCA's right ear stays with him")
    return ("PROPS REGISTRY for this episode — background furniture may exist but never "
            "becomes a gag, never moves on its own and never duplicates; the registry: "
            + "; ".join(partes) + ".")


def contas_do_registro(e):
    """Linha de CONTAGEM explicita (a tecnica que fechou balde/grelha no v7):
    EXACTLY ONE <objeto> para tudo que o registro declara - o prompt do clipe/da
    ancora ganha a guarda antes de o juiz contar."""
    itens = []
    for o in (e.get("objetos_plantados") or []):
        nome = str(o.get("objeto") or o.get("nome") or "").strip()
        try:
            q = int(o.get("contagem", 1) or 1)
        except Exception:
            q = 1
        if nome and q == 1:
            pos = str(o.get("posicao", "") or "").strip()
            if pos:
                itens.append("EXACTLY ONE %s (%s)" % (nome, pos))
            else:
                itens.append("EXACTLY ONE " + nome)
    if not itens:
        return ""
    return (" There is " + ", ".join(itens) + " in the whole frame - no second unit of any "
            "of them ever appears, nothing duplicates, nothing teleports and every item "
            "stands exactly at the place declared between parentheses, never in a hand that "
            "the place does not name; every paper, page, envelope and cloth is perfectly "
            "blank with no writing, no lines and no marks; the window glass is plain and "
            "clear with no pattern, no cross, no symbols, no lettering anywhere; plain "
            "containers and cloths on the benches are background. ")


def descrever_ancora(key, png):
    import base64
    SYS = ("Descreva este frame de claymation como um ESTADO DE CENA em UMA frase em "
           "ingles, objetiva: quem esta onde, o que cada um segura, que objetos existem "
           "e onde estao, estado do piso. Sem interpretacao, so o que se ve. "
           'Responda JSON: {"estado": "uma frase EN"}')
    parts = [{"type": "image", "data": base64.b64encode(Path(png).read_bytes()).decode(),
              "mime_type": "image/png"}]
    tx = qc_visao._call(key, SYS, parts, max_tokens=2000)
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


def render_ancora(key, ep_dir, setdir, slug, st_c01, estado_planejado, props, cliente,
                  contas=""):
    refs = ep_dir / "refs"
    refs.mkdir(exist_ok=True)
    head = st_c01["prompt"][:st_c01["prompt"].find("AT START:")].rstrip()
    PROMPT = (head + " AT START: " + estado_planejado + ". "
              "[Shot 1] the opening wide frame exactly as established: TEO at frame left, "
              "JUCA at frame right, all props in place; both puppets hold their positions, "
              "breathing." + contas + " AT END: the same wide frame, unchanged. They do not speak and "
              "their mouths do not move, but they breathe, swallow and react with their "
              "whole bodies."
              "\noverall_soundscape: room tone of the enclosed set, water dripping slowly."
              "\nnon_diegetic_music: N/A")
    for tent in range(TENT_ANCORA):
        slug_a = slug + "_ancora" + ("" if tent == 0 else "_r%d" % tent)
        st = dict(st_c01)
        st["output_filename"] = slug_a
        st["video_length"] = "5s"
        st["seed"] = 8001 + tent
        st.pop("image_start", None)
        st["prompt"] = PROMPT
        sdf = setdir / (slug_a + "_settings.json")
        sdf.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n=== ANCORA · tentativa %d/%d · seed %d ===" % (tent + 1, TENT_MAX, st["seed"]),
              flush=True)
        t0 = time.time()
        r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", "SMOKE_ANC"], cwd=CWD)
        print("  render rc=%d · %.1f min" % (r.returncode, (time.time() - t0) / 60), flush=True)
        cands = [p for p in OUT.glob(slug_a + "*.mp4") if p.stat().st_mtime >= t0 - 5]
        if r.returncode != 0 or not cands:
            continue
        mp4 = max(cands, key=lambda p: p.stat().st_mtime)
        dest = refs / "ancora_smoke.png"
        subprocess.run([FF, "-y", "-ss", "4.4", "-i", str(mp4), "-frames:v", "1", str(dest)],
                       capture_output=True)
        j = qc_visao.gate_ancora(key, str(dest), estado=estado_planejado, props=props,
                                 cliente=cliente)
        print("  GATE ANCORA: %s - %s" % (j.get("veredito"), j.get("motivo", "")), flush=True)
        print("    cenario=%s nao_plantados=%s extras=%s"
              % (j.get("cenario_violado"), j.get("objetos_nao_plantados"),
                 j.get("personagens_extras")), flush=True)
        if j.get("veredito") == "APROVADA":
            return dest
        print("  ancora reprovada - retry seed+1", flush=True)
    return None


def render_com_gate(key, ep_dir, setdir, slug_base, n, total, ancora_png, estado_real,
                    cliente, seed_base, props, estado_end, contas=""):
    st_base = json.loads((setdir / (slug_base + "_settings.json")).read_text(encoding="utf-8"))
    curto = "c%02d" % n
    refs = ep_dir / "refs"
    refs.mkdir(exist_ok=True)
    tentativas = []
    for tent in range(TENT_MAX):
        sufixo = "_sm" + ("" if tent == 0 else "_r%d" % tent)
        slug = slug_base + sufixo
        st = dict(st_base)
        st["output_filename"] = slug
        st["seed"] = seed_base + tent
        st["image_start"] = str(ancora_png)
        st["image_prompt_type"] = "S"
        st["prompt"] = (re.sub(r"AT START: (.+?)\. \[Shot",
                               "AT START: " + estado_real.replace("\\", "") + ". [Shot",
                               st_base["prompt"], count=1, flags=16) + contas + ALINHA)
        sdf = setdir / (slug + "_settings.json")
        sdf.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n=== %s · tentativa %d/%d · seed %d · cliente=%s ==="
              % (slug, tent + 1, TENT_MAX, st["seed"], "SIM" if cliente else "NAO"), flush=True)
        t0 = time.time()
        r = subprocess.run([PY, GEN, "--settings", str(sdf), "--tag", "SMOKE_C%02d" % n],
                           cwd=CWD)
        dur = (time.time() - t0) / 60
        cand = [p for p in OUT.glob(slug + "*.mp4") if p.stat().st_mtime >= t0 - 5]
        print("  render rc=%d · %.1f min" % (r.returncode, dur), flush=True)
        if r.returncode != 0 or not cand:
            tentativas.append({"slug": slug, "seed": st["seed"], "rc": r.returncode,
                               "falha": "render"})
            continue
        mp4 = max(cand, key=lambda p: p.stat().st_mtime)
        sc = scan_ceu.escanear(mp4, passo=0.5, faixa=0.28, limiar=0.10)
        print("  SCAN CEU: %s%s" % (sc["veredito"], "" if not sc["violacoes"] else
              " " + "; ".join("%.1f-%.1fs pico %.0f%%" % (v["ini_s"], v["fim_s"],
                                                          v["pico"] * 100)
                              for v in sc["violacoes"])), flush=True)
        if sc["violacoes"]:
            tentativas.append({"slug": slug, "seed": st["seed"], "mp4": str(mp4),
                               "scan_ceu": sc, "falha": "ceu"})
            continue
        f99 = refs / ("ancora_smoke_%s.png" % curto)
        f50 = refs / ("meio_smoke_%s.png" % curto)
        f02 = refs / ("inicio_smoke_%s.png" % curto)
        f20 = refs / ("corte1_smoke_%s.png" % curto)
        f30 = refs / ("corte2_smoke_%s.png" % curto)
        f08 = refs / ("emenda_smoke_%s.png" % curto)
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
                    j = qc_visao.gate_ancora(key, str(dst), estado=est, props=props,
                                             cliente=cliente, inserto=ins)
                    verds[ts] = j
                    print("  GATE f%s%s: %s - %s"
                          % (ts, " (inserto)" if ins else "", j.get("veredito"),
                             j.get("motivo", "")), flush=True)
                break
            except BaseException as e:
                verds = {}
                print("  gate INDISPONIVEL (%s) - espero 120s e repito (%d/15)"
                      % (str(e)[:200], tg + 1), flush=True)
                time.sleep(120)
        if not verds:
            tentativas.append({"slug": slug, "seed": st["seed"], "mp4": str(mp4),
                               "falha": "gate_indisponivel"})
            print("  gate indisponivel por 30 min - CADEIA PAUSADA (retome depois)", flush=True)
            raise SystemExit(7)
        j99 = verds["9.9"]
        tentativas.append({"slug": slug, "seed": st["seed"], "dur_min": round(dur, 1),
                           "mp4": str(mp4), "psnr_f02": ps, "scan_ceu": sc,
                           "gate_ancora": j99, "gate_frames": dict(verds)})
        if all(_ok(verds[t], ins) for t, _d, _e, ins in planos):
            return mp4, f99, tentativas
        print("  gate reprovou - retry seed+1", flush=True)
    return None, None, tentativas


def fase_final(ep_dir, slug, feitos, total):
    final = ep_dir / "final_smoke"
    final.mkdir(exist_ok=True)
    for f in final.glob("*.mp4"):
        f.unlink()
    clips = {}
    for f in feitos:
        if f.get("mp4") and (f.get("aprovado") or f.get("fallback")):
            clips[f["curto"]] = f["mp4"]
    ordem = ["c%02d" % i for i in range(1, total + 1)]
    faltam = [c for c in ordem if c not in clips]
    if faltam:
        print("XX cadeia incompleta: faltam %s — montagem cancelada." % faltam, flush=True)
        return None
    import shutil
    for c in ordem:
        src = Path(clips[c])
        dst = final / (c + "_" + src.name)
        shutil.copy2(src, dst)
        print("stage: %s (%.1f MB)" % (dst.name, dst.stat().st_size / 1048576), flush=True)
    saida = ep_dir / (slug + "_SMOKE60.mp4")
    r = subprocess.run([PY, str(PIPE / "pos_producao.py"), "--pasta", str(final),
                        "--padrao", "*.mp4", "--cortar-meio", "--saida", str(saida)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout[-700:], flush=True)
    r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(final),
                        "--padrao", "*.mp4", "--settings", str(ep_dir / "settings"),
                        "--saida", str(ep_dir / "qc_smoke.json")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout[-1200:], flush=True)
    if saida.exists():
        print("\n>>> FUMACA 60 s PRONTA: %s (%.1f MB)"
              % (saida, saida.stat().st_size / 1048576), flush=True)
        return saida
    print("XX pos-producao nao gerou o arquivo final", flush=True)
    return None


def main():
    m, ep_dir, e = carregar()
    slug = ep_dir.name
    setdir = ep_dir / "settings"
    log = open(ep_dir / "smoke_run.log", "a", encoding="utf-8")
    sys.stdout = _Tee(sys.stdout, log)
    sys.stderr = _Tee(sys.stderr, log)
    print("\n===== SMOKE 60 s · %s · largada %s ====="
          % (slug, time.strftime("%Y-%m-%d %H:%M:%S")), flush=True)
    KEY = qc_visao._chave()
    shots = e.get("shots") or []
    total = len(shots)
    clipes = settings_clipes(slug, setdir, e)
    if len(clipes) != total:
        raise SystemExit("XX settings esperados %d, encontrados %d em %s"
                         % (total, len(clipes), setdir))
    props = props_do_episodio(e)
    CONTAS = contas_do_registro(e)
    print("PROPS: %s" % props, flush=True)
    print("CONTAS: %s" % CONTAS, flush=True)

    if "--dry" in sys.argv:
        for i, f in enumerate(clipes, 1):
            sb = json.loads(f.read_text(encoding="utf-8"))
            print("c%02d: len=%d cliente=%s dur=%s"
                  % (i, len(sb["prompt"]), i in (1, total), sb.get("video_length")), flush=True)
        return

    banco_f = ep_dir / "smoke_bancados.json"
    banco = json.loads(banco_f.read_text(encoding="utf-8")) if banco_f.exists() else {}
    feitos = []

    def salvar_relatorio():
        (ep_dir / "smoke_relatorio.json").write_text(
            json.dumps(feitos, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── FASE 0: ancora de abertura ───────────────────────────────────────────
    ancora_existente = ep_dir / "refs" / "ancora_smoke.png"
    if "ancora" in banco:
        ancora = Path(banco["ancora"])
        print("\n>>> ANCORA BANCADA: %s" % ancora, flush=True)
    elif ancora_existente.exists():
        ancora = ancora_existente
        print("\n>>> ANCORA EXISTENTE reaproveitada (ja renderizada): %s" % ancora, flush=True)
        banco["ancora"] = str(ancora)
        banco_f.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        st_c01 = json.loads(clipes[0].read_text(encoding="utf-8"))
        estado0 = str(shots[0].get("estado_in") or "").strip()
        if not estado0:
            mo = re.search(r"AT START: (.+?)\. \[Shot", st_c01["prompt"])
            estado0 = mo.group(1) if mo else "TEO at frame left and JUCA at frame right"
        cliente0 = bool(re.search(r"client|cliente", estado0, re.I))
        ancora = render_ancora(KEY, ep_dir, setdir, slug, st_c01, estado0, props,
                               cliente0, contas=CONTAS)
        if not ancora:
            raise SystemExit("XX ancora reprovada nas 3 tentativas — cadeia cancelada.")
        banco["ancora"] = str(ancora)
        banco_f.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── FASE 1: cadeia de clipes ─────────────────────────────────────────────
    for i, f in enumerate(clipes, 1):
        curto = "c%02d" % i
        slug_base = f.stem.replace("_settings.json", "")
        if curto in banco.get("clipes", {}):
            print("\n>>> %s BANCADO — pulando" % curto, flush=True)
            feitos.append(banco["clipes"][curto])
            ancora = Path(banco["clipes"][curto]["ancora_out"])
            salvar_relatorio()
            continue
        st_base = json.loads(f.read_text(encoding="utf-8"))
        mo_end = re.search(r"AT END: (.+?)\.?(?:\n|$)", st_base["prompt"])
        estado_end = mo_end.group(1) if mo_end else ""
        est_real = descrever_ancora(KEY, ancora)
        print("\n>>> estado REAL da ancora (%s): %s" % (curto, est_real), flush=True)
        mp4, f99, tentativas = render_com_gate(
            KEY, ep_dir, setdir, slug_base, i, total, ancora, est_real,
            cliente=(i in (1, total)), seed_base=8000 + 100 * i, props=props,
            estado_end=estado_end, contas=CONTAS)
        if not mp4:
            fb = ep_dir / "refs" / ("ancora_smoke_%s.png" % curto)
            mp_fb = next((t["mp4"] for t in reversed(tentativas) if t.get("mp4")), None)
            if fb.exists() and mp_fb:
                print("XX %s: tentativas reprovadas — CONTINUANDO com fallback controlado."
                      % curto, flush=True)
                feitos.append({"slug": slug_base, "curto": curto, "mp4": mp_fb,
                               "aprovado": False, "fallback": True,
                               "ancora_out": str(fb), "tentativas": tentativas})
                ancora = fb
                banco.setdefault("clipes", {})[curto] = feitos[-1]
                banco_f.write_text(json.dumps(banco, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
                salvar_relatorio()
                continue
            print("XX %s nao aprovado e sem fallback — cadeia para aqui." % slug_base,
                  flush=True)
            feitos.append({"slug": slug_base, "curto": curto, "aprovado": False,
                           "tentativas": tentativas})
            salvar_relatorio()
            break
        feitos.append({"slug": slug_base, "curto": curto, "mp4": str(mp4), "aprovado": True,
                       "ancora_out": str(f99), "tentativas": tentativas})
        ancora = f99
        banco.setdefault("clipes", {})[curto] = feitos[-1]
        banco_f.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
        salvar_relatorio()

    salvar_relatorio()
    n_ok = sum(1 for f in feitos if f.get("aprovado"))
    print("\n>>> CADEIA SMOKE: %d/%d clipes aprovados" % (n_ok, total), flush=True)

    # ── FASE 2: montagem final ───────────────────────────────────────────────
    saida = fase_final(ep_dir, slug, feitos, total)
    print("\n===== SMOKE 60 s FIM %s =====" % time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
    if not saida:
        sys.exit(3)


if __name__ == "__main__":
    main()
