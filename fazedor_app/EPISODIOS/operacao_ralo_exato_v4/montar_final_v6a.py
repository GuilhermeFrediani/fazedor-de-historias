# -*- coding: utf-8 -*-
"""Monta o FINAL v6a PATCH: c01-c03 do v5 (limpos no resumo) + c04-c06 NOVOS da
cadeia patch (gate duplo) -> pos-producao COM --cortar-meio (o v5 FINAL nao teve
o trim; o resumo marcou ar morto 41-43s) -> gate episodico.

Nao toca no v5_FINAL nem na pasta final/ do v5 — tudo em final_v6a/ e _v6a_PATCH.
"""
import json, re, subprocess, sys, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PY = r"C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")
EP = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4")
PIPE = EP.parent.parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import qc_visao
FINAL_DIR = EP / "final_v6a"
FINAL_DIR.mkdir(exist_ok=True)
SAIDA = EP / "operacao_ralo_exato_v4_v6a_PATCH.mp4"

# 0) os 3 novos da cadeia patch — exige gate duplo APROVADA no relatorio
rel = json.loads((EP / "cadeia_patch_relatorio.json").read_text(encoding="utf-8"))
novos = {}
for f in rel:
    ga, gm = f.get("gate_ancora", {}), f.get("gate_meio", {})
    if f.get("aprovado") and ga.get("veredito") == "APROVADA" and gm.get("veredito") == "APROVADA":
        novos[f["curto"]] = f["mp4"]
    elif f.get("fallback") and f.get("mp4"):
        novos[f["curto"]] = f["mp4"]
        print("!! %s entra como FALLBACK (gate nao aprovou) — corte de hoje, "
              "sujeito a nova rodada" % f["curto"])
if len(novos) < 3:
    print("XX cadeia patch incompleta (%d/3 disponiveis) — emenda cancelada." % len(novos))
    sys.exit(2)
print("novos da cadeia: " + ", ".join("%s=%s" % (k, Path(v).name) for k, v in sorted(novos.items())))

# 1) c01 probe (igual ao v5): ultimo frame = ancora_limpa_t3
ref = EP / "refs" / "ancora_limpa_t3.png"
cands = sorted(glob.glob(str(OUT / "operacao_ralo_exato_v4_c01_ligacao*.mp4")),
               key=lambda p: Path(p).stat().st_mtime, reverse=True)
c01 = None
for cand in cands:
    tmp = FINAL_DIR / "_probe.png"
    subprocess.run([FF, "-y", "-ss", "9.9", "-i", cand, "-frames:v", "1", str(tmp)], capture_output=True)
    ps = subprocess.run([FF, "-i", str(tmp), "-i", str(ref), "-lavfi", "psnr", "-f", "null", "-"],
                        capture_output=True, text=True)
    m = re.search(r"average:([\d.]+)", ps.stderr)
    db = float(m.group(1)) if m else 0
    print("c01 candidato: %s · PSNR %.1f dB" % (Path(cand).name, db))
    if db >= 30:
        c01 = cand
        break
if not c01:
    print("XX nenhum c01 casa com a ancora aprovada")
    sys.exit(2)
print("c01 escolhido: %s" % Path(c01).name)

# 2) palco: c01-c03 do v5 + c04-c06 novos
aprovados = [
    ("c01", c01),
    ("c02", OUT / "operacao_ralo_exato_v4_c02_cadeia.mp4"),
    ("c03", OUT / "operacao_ralo_exato_v4_c03_primeira_falha_v2.mp4"),
    ("c04", Path(novos["c04"])),
    ("c05", Path(novos["c05"])),
    ("c06", Path(novos["c06"])),
]
for f in FINAL_DIR.glob("*.mp4"):
    f.unlink()
for nome, src in aprovados:
    dst = FINAL_DIR / (nome + "_" + Path(src).name)
    import shutil
    shutil.copy2(src, dst)
    print("stage: %s (%.1f MB)" % (dst.name, dst.stat().st_size / 1048576))

# 3) pos-producao COM trim de ar morto no meio (fix do resumo: 41-43s)
r = subprocess.run([PY, str(PIPE / "pos_producao.py"), "--pasta", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--cortar-meio",
                    "--saida", str(SAIDA)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-700:])

# 4) gate episodico no FINAL v6a
r = subprocess.run([PY, str(PIPE / "qc_visao.py"), "--clipes", str(FINAL_DIR),
                    "--padrao", "*.mp4", "--settings", str(EP / "settings"),
                    "--saida", str(EP / "qc_final_v6a.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[-900:])
if SAIDA.exists():
    print("\n>>> FINAL v6a PATCH:", SAIDA, "(%.1f MB)" % (SAIDA.stat().st_size / 1048576))
