# -*- coding: utf-8 -*-
"""Cadeia completa v4 — renders (6x ~15 min) + concat cru + PÓS-PRODUÇÃO (o passo novo).
O fumaca_v4.py do auditor termina na validação; este script executa o resto:
  1. gen_test por settings (settings já escritos pelo --seco)
  2. concat cru (segurança)
  3. pos_producao.py --analisar  (mede ar morto + volume)
  4. pos_producao.py --pasta --saida FINAL  (-14 LUFS + punch-in + faststart)
Saída final: EPISODIOS\\operacao_ralo_exato_v4\\operacao_ralo_exato_v4_FINAL.mp4"""
import os, sys, glob, time, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
GEN = r"C:\Users\Guilherme\Documents\Projeto Padrão\gen_test.py"
CWD = r"C:\Users\Guilherme\Documents\Projeto Padrão"
OUTDIR = r"C:\pinokio\api\wan2gp-amd\app\outputs"
EP = r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4"
SETDIR = os.path.join(EP, "settings")
POS = r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\pipeline\pos_producao.py"

CLIPES = [
    ("operacao_ralo_exato_v4_c01_ligacao",         "V4_C01"),
    ("operacao_ralo_exato_v4_c02_chegada",         "V4_C02"),
    ("operacao_ralo_exato_v4_c03_primeira_falha",  "V4_C03"),
    ("operacao_ralo_exato_v4_c04_jeitinho",        "V4_C04"),
    ("operacao_ralo_exato_v4_c05_escalada",        "V4_C05"),
    ("operacao_ralo_exato_v4_c06_climax",          "V4_C06"),
]

def mp4s_antes():
    return {f for f in glob.glob(os.path.join(OUTDIR, "*.mp4"))}

feitos = []
for slug, tag in CLIPES:
    st = os.path.join(SETDIR, slug + "_settings.json")
    print("\n=== [%s] rendendo %s …" % (tag, slug), flush=True)
    t0 = time.time()
    antes = mp4s_antes()
    r = subprocess.run([PY, GEN, "--settings", st, "--tag", tag], cwd=CWD)
    dur = (time.time() - t0) / 60.0
    mp4 = None
    for f in glob.glob(os.path.join(OUTDIR, slug + "*.mp4")):
        mp4 = f
    if not mp4:
        novos = [f for f in mp4s_antes() - antes]
        if novos:
            mp4 = max(novos, key=os.path.getmtime)
    if r.returncode == 0 and mp4:
        feitos.append(mp4)
        print("=== [%s] OK em %.1f min → %s" % (tag, dur, os.path.basename(mp4)), flush=True)
    else:
        print("=== [%s] FALHOU rc=%d após %.1f min — abortando." % (tag, r.returncode, dur), flush=True)
        sys.exit(1)

print("\n=== concat cru (%d clipes) …" % len(feitos), flush=True)
lista = os.path.join(EP, "fumaca_lista.txt")
with open(lista, "w", encoding="utf-8") as f:
    for p in feitos:
        f.write("file '" + p.replace("\\", "/") + "'\n")
import imageio_ffmpeg
ff = imageio_ffmpeg.get_ffmpeg_exe()
cru = os.path.join(EP, "operacao_ralo_exato_v4_fumaca_6clipes.mp4")
r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", cru],
                   capture_output=True, text=True)
print("concat cru rc=%d (%.1f MB)" % (r.returncode, os.path.getsize(cru) / 1048576.0))

print("\n=== PÓS-PRODUÇÃO — passo 4a: analisar ===", flush=True)
r = subprocess.run([PY, POS, "--analisar", OUTDIR], cwd=os.path.dirname(POS))
print("analisar rc=%d" % r.returncode, flush=True)

print("=== PÓS-PRODUÇÃO — passo 4b: montar FINAL (-14 LUFS + punch-in + faststart) ===", flush=True)
final = os.path.join(EP, "operacao_ralo_exato_v4_FINAL.mp4")
r = subprocess.run([PY, POS, "--pasta", OUTDIR, "--saida", final], cwd=os.path.dirname(POS))
print("montar rc=%d" % r.returncode, flush=True)
if os.path.exists(final):
    print("\n>>> FINAL:", final, "(%.1f MB)" % (os.path.getsize(final) / 1048576.0))
print(">>> FUMACA v4 + POS-PRODUCAO CONCLUIDAS")
