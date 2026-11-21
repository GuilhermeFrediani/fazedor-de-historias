# -*- coding: utf-8 -*-
"""CADEIA LIMPA — clipe 1 higiênico → gate de âncora → ponte do clipe 2 → gate das pontas.
Regra nova da série: NENHUM clipe entra na cadeia sem âncora APROVADA pelo gate de visão.
Retry automático: seed+1 (max 2 tentativas extras) se a âncora reprovar.
Saídas: settings *cadeia*.json + MP4s + cadeia_limpa_relatorio.json"""
import json, subprocess, sys, time, base64, urllib.request
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
import qc_visao  # gate_ancora + chave

KEY = qc_visao._chave()
ALINHA = (" For the target video, at 0.00 seconds into the target video, <Picture 1> "
          "(from [Shot 1]) is fully referenced.")
SLUG1, TAG1 = "operacao_ralo_exato_v4_c01_ligacao", "CADEIA_C01"
SLUG2, TAG2 = "operacao_ralo_exato_v4_c02_cadeia", "CADEIA_C02"


def render(slug, tag):
    st = str(SETDIR / (slug + "_settings.json"))
    t0 = time.time()
    r = subprocess.run([PY, GEN, "--settings", st, "--tag", tag], cwd=CWD)
    mp4s = list(OUT.glob(slug + "*.mp4"))
    ok = r.returncode == 0 and mp4s
    print("  render %s: rc=%d · %.1f min · %s" % (tag, r.returncode, (time.time() - t0) / 60,
                                                  mp4s[0].name if mp4s else "SEM MP4"), flush=True)
    return (mp4s[0] if ok else None)


def ultimo_frame(mp4, dst):
    subprocess.run([FF, "-y", "-ss", "9.9", "-i", str(mp4), "-frames:v", "1", str(dst)], capture_output=True)
    return dst


def gate_ancora_arquivo(png, estado=""):
    j = qc_visao.gate_ancora(KEY, str(png), estado)
    print("  GATE ANCORA: %s — %s" % (j.get("veredito"), j.get("motivo", "")), flush=True)
    print("  extras=%s flutuantes=%s" % (j.get("personagens_extras"), j.get("objetos_flutuantes")), flush=True)
    return j


rel = {"c01": [], "c02": {}}

# ── 1) CLIPE 1 LIMPO (retry com seed+1 ate a ancora passar, max 3 tentativas) ──
st1 = json.loads((SETDIR / (SLUG1 + "_settings.json")).read_text(encoding="utf-8"))
anchor_aprovada, mp4_1, ancora_png = False, None, None
for tent in range(3):
    st1["seed"] = 7001 + tent
    (SETDIR / (SLUG1 + "_settings.json")).write_text(json.dumps(st1, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== CLIPE 1 · tentativa %d · seed %d ===" % (tent + 1, st1["seed"]), flush=True)
    mp4 = render(SLUG1, TAG1 + ("" if tent == 0 else "_t%d" % (tent + 1)))
    if not mp4:
        continue
    png = ultimo_frame(mp4, EP / "refs" / ("ancora_limpa_t%d.png" % (tent + 1)))
    j = gate_ancora_arquivo(png, st1["prompt"].split("AT START: ")[-1].split(". [Shot")[0])
    rel["c01"].append({"tentativa": tent + 1, "seed": st1["seed"], "gate": j})
    if j.get("veredito") == "APROVADA":
        anchor_aprovada, mp4_1, ancora_png = True, mp4, png
        break

# ── 2) PONTE DO CLIPE 2 a partir da âncora limpa ──
if anchor_aprovada:
    st2 = json.loads((SETDIR / (SLUG2.replace("_cadeia", "_chegada") + "_settings.json")).read_text(encoding="utf-8"))
    st2["output_filename"] = SLUG2
    st2["image_start"] = str(ancora_png)
    st2["image_prompt_type"] = "S"
    st2["prompt"] = st2["prompt"] + ALINHA
    (SETDIR / (SLUG2 + "_settings.json")).write_text(json.dumps(st2, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== CLIPE 2 · ponte a partir da ancora limpa ===", flush=True)
    mp4_2 = render(SLUG2, TAG2)
    if mp4_2:
        ini = ultimo_frame(mp4_2, EP / "refs" / "c02_cadeia_primeiro.png").replace("primeiro", "primeiro")
        # gate do clipe 2: 4 frames vs estado prometido
        r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(OUT),
                            "--padrao", SLUG2 + "_*.mp4", "--settings", str(SETDIR),
                            "--saida", str(EP / "qc_cadeia_c02.json")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print(r.stdout[-800:], flush=True)
        rel["c02"]["mp4"] = str(mp4_2)
        # âncora do clipe 2 (para o clipe 3, se aprovada)
        j2 = gate_ancora_arquivo(ultimo_frame(mp4_2, EP / "refs" / "ancora_c02.png"))
        rel["c02"]["gate_ancora"] = j2
else:
    print("\nXX ANCORa do clipe 1 REPROVADA 3x — cadeia NAO prossegue (regra da serie).", flush=True)

(EP / "cadeia_limpa_relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n>>> relatorio: " + str(EP / "cadeia_limpa_relatorio.json"), flush=True)
print(">>> CADEIA LIMPA CONCLUIDA — c01 aprovado: %s · c02 ponte: %s" % (anchor_aprovada, bool(rel.get("c02", {}).get("mp4"))))
