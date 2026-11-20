# -*- coding: utf-8 -*-
# calibra2.py — fecha a calibracao: c05@2.5s (pico 28%), c06@6.0s (8% constante)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scan_ceu import _frame_rgb, _fracao_ceu
import numpy as np
from PIL import Image

BASE = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4\final_v6a")
OUT = Path(r"C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\EPISODIOS\operacao_ralo_exato_v4\refs\calibracao_scan")
amostras = {
    "c05_pico_25s": ("c05_operacao_ralo_exato_v4_c05_escalada_v6a_r2(5).mp4", 2.5),
    "c06_cauda_60s": ("c06_operacao_ralo_exato_v4_c06_climax_v6a.mp4", 6.0),
}
for nome, (arq, ts) in amostras.items():
    arr = _frame_rgb(BASE / arq, ts, 480)
    topo = arr[: int(arr.shape[0] * 0.28), :, :]
    Image.fromarray(topo.astype(np.uint8)).save(OUT / (nome + ".png"))
    print("%-14s fracao=%.1f%%" % (nome, _fracao_ceu(arr, 0.28) * 100))
