# -*- coding: utf-8 -*-
# calibra_scan.py — prova visual: recorta a FAIXA SUPERIOR nos instantes-chave
# e imprime a serie completa de fracao-azul por clipe (para escolher o limiar).
import sys, json, subprocess, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scan_ceu import _frame_rgb, _fracao_ceu, escanear
import numpy as np
from PIL import Image

BASE = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4\final_v6a")
OUT = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4\refs\calibracao_scan")
OUT.mkdir(parents=True, exist_ok=True)

amostras = {
    "c04_ruido_45s": ("c04_operacao_ralo_exato_v4_c04_jeitinho_v6a_r2.mp4", 4.5),
    "c05_ceu_50s":   ("c05_operacao_ralo_exato_v4_c05_escalada_v6a_r2(5).mp4", 5.0),
    "c06_ceu_51s":   ("c06_operacao_ralo_exato_v4_c06_climax_v6a.mp4", 1.0),
    "c02_ruido_55s": ("c02_operacao_ralo_exato_v4_c02_cadeia.mp4", 5.0),
}
print("=== RECORTES DA FAIXA SUPERIOR (0-28% da altura) ===")
for nome, (arq, ts) in amostras.items():
    arr = _frame_rgb(BASE / arq, ts, 480)
    topo = arr[: int(arr.shape[0] * 0.28), :, :]
    Image.fromarray(topo.astype(np.uint8)).save(OUT / (nome + ".png"))
    print("  %-16s %s @ %.1fs  fracao_azul=%.1f%%" % (nome, arq[:3], ts, _fracao_ceu(arr, 0.28) * 100))

print()
print("=== SERIE COMPLETA POR CLIPE (fracao azul %% a cada 0.5s) ===")
for arq in sorted(BASE.glob("c0*.mp4")):
    r = escanear(arq, passo=0.5)
    serie = []
    ts = 0.1
    while ts < r["dur_s"] - 0.05:
        serie.append((round(ts, 1), round(_fracao_ceu(_frame_rgb(arq, ts, 320), 0.28) * 100, 1)))
        ts += 0.5
    print("%s  dur=%.1fs" % (arq.name[:3], r["dur_s"]))
    print("   " + "  ".join("%.1fs:%.0f%%" % (t, v) for t, v in serie))
