# -*- coding: utf-8 -*-
"""scan_ceu.py — REDE DENSA de invariante de set (0 GPU, 0 API, local).
O gate semantico (2 frames/clipe) deixou o ceu de 43-54s passar INTEIRO entre
as amostras. Isto varre TODO o clipe: 1 frame a cada 0.5s, faixa superior do
quadro (teto), metrica de azul-ceu (B dominante + brilho alto) — aco/cortina/
luminarias nunca sao azuis-dominantes. Frame com >2% de ceu na faixa = violacao.

Uso:
  python scan_ceu.py --clipe video.mp4 [--passo 0.5] [--faixa 0.28] [--limiar 0.02]
  python scan_ceu.py --pasta DIR --padrao "*.mp4"
Saida: JSON com faixas violadas (ini_s, fim_s, pico) + veredito.
"""
import argparse, json, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
import numpy as np
from PIL import Image
import tempfile, os


def _frame_rgb(mp4, ts, w=320):
    """Extrai 1 frame pequeno em RGB numpy (320 de largura — medida, nao beleza)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    subprocess.run([FF, "-y", "-ss", str(ts), "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale=%d:-1" % w, tmp.name], capture_output=True)
    arr = np.asarray(Image.open(tmp.name).convert("RGB"), dtype=np.int16)
    os.unlink(tmp.name)
    return arr


def _fracao_ceu(arr, faixa):
    """Fracao de pixels azul-ceu na faixa superior (0..faixa da altura)."""
    topo = arr[: int(arr.shape[0] * faixa), :, :]
    r, g, b = topo[:, :, 0], topo[:, :, 1], topo[:, :, 2]
    ceu = (b > 150) & (b > r + 25) & (b > g + 15)
    return float(ceu.mean())


def escanear(mp4, passo=0.5, faixa=0.28, limiar=0.02, dur_max=None):
    """Varre o clipe inteiro. Retorna relatorio com as faixas violadas."""
    p = subprocess.run([FF, "-i", str(mp4)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    import re
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 10.0
    if dur_max:
        dur = min(dur, dur_max)
    ts, vals, viol = 0.1, [], []
    while ts < dur - 0.05:
        f = _fracao_ceu(_frame_rgb(mp4, ts, 320), faixa)
        vals.append((round(ts, 1), round(f, 4)))
        ts += passo
    # agrega em faixas contiguas de violacao
    ini = None
    for t, v in vals:
        if v > limiar and ini is None:
            ini = t
        elif v <= limiar and ini is not None:
            viol.append({"ini_s": ini, "fim_s": t, "pico": max(x for tt, x in vals if ini <= tt <= t)})
            ini = None
    if ini is not None:
        viol.append({"ini_s": ini, "fim_s": round(dur, 1),
                     "pico": max(x for tt, x in vals if tt >= ini)})
    return {"clipe": str(mp4), "dur_s": round(dur, 1), "passo_s": passo,
            "faixa_topo": faixa, "limiar": limiar,
            "amostras": len(vals), "violacoes": viol,
            "veredito": "REPROVADA" if viol else "APROVADA"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--clipe")
    ap.add_argument("--pasta")
    ap.add_argument("--padrao", default="*.mp4")
    ap.add_argument("--passo", type=float, default=0.5)
    ap.add_argument("--faixa", type=float, default=0.28)
    # calibrado em 2026-11-20 contra o v6a (prova visual em refs/calibracao_scan/):
    #   ruido estrutural do set (janela atras da cortina, aco azulado): 0-8%
    #   ceu real (telhado aberto): 17-31%  -> limiar 10% separa com 2x de margem
    ap.add_argument("--limiar", type=float, default=0.10)
    a = ap.parse_args()
    alvos = []
    if a.clipe:
        alvos.append(Path(a.clipe))
    elif a.pasta:
        alvos = sorted(Path(a.pasta).glob(a.padrao))
    for mp4 in alvos:
        r = escanear(mp4, a.passo, a.faixa, a.limiar)
        tag = "CEU!" if r["violacoes"] else "ok  "
        faixas = "; ".join("%.1f-%.1fs pico %.0f%%" % (v["ini_s"], v["fim_s"], v["pico"] * 100)
                           for v in r["violacoes"]) or "-"
        print("[%s] %-58s %s" % (tag, Path(mp4).name, faixas), flush=True)
