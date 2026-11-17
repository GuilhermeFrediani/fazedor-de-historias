# -*- coding: utf-8 -*-
"""
pos_producao.py — a camada que nenhum prompt resolve.

O gerador entrega 6 clipes crus. Clipe cru nao tem graca: tem ar morto, audio mudo
e plano fixo. Esta camada faz, com ffmpeg, o que um editor faria:

  1. MEDE o ar morto (freezedetect) e o nivel de audio (volumedetect);
  2. NORMALIZA o audio para -14 LUFS (o material atual esta em -38 dB: 24 dB abaixo
     do padrao do YouTube);
  3. CORTA o ar morto do fim de cada clipe (onde os bonecos so ficam plantados);
  4. ABRE UM CORTE seco no meio do clipe (punch-in de 1,25x) - da ritmo sem regerar;
  5. MISTURA uma cama musical baixa (-26 dB) por baixo, se voce tiver um arquivo;
  6. CONCATENA com xfade de 3 frames (o corte de massinha pede respiro de 1 quadro).

Uso:
    python pos_producao.py --pasta CLIPES --saida EP_FINAL.mp4 [--musica bed.mp3] [--dry]
    python pos_producao.py --analisar CLIPES          # so mede ar morto e volume
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()          # caminho absoluto do ffmpeg embutido
_probe = Path(FFMPEG).parent / "ffprobe.exe"
FFPROBE = str(_probe) if _probe.exists() else None  # imageio nao embute ffprobe


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def duracao(arq):
    if FFPROBE:
        r = _run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=nw=1:nk=1", str(arq)])
        try:
            return float(r.stdout.strip())
        except ValueError:
            pass
    # fallback sem ffprobe: parse do "Duration:" do ffmpeg -i
    r = _run([FFMPEG, "-hide_banner", "-i", str(arq)])
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr)
    if m:
        h, mnt, s = m.groups()
        return int(h) * 3600 + int(mnt) * 60 + float(s)
    return 0.0


def nivel_audio(arq):
    """Devolve (media_dB, pico_dB)."""
    r = _run([FFMPEG, "-hide_banner", "-i", str(arq), "-af", "volumedetect", "-f", "null", "-"])
    media = pico = None
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
    if m:
        media = float(m.group(1))
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
    if m:
        pico = float(m.group(1))
    return media, pico


def ar_morto(arq, silencio_s=1.0, ruido_db=-45):
    """Usa freezedetect para achar trechos congelados (bonecos plantados).
    Devolve lista de (inicio, fim) em segundos."""
    r = _run([FFMPEG, "-hide_banner", "-i", str(arq),
              "-vf", "freezedetect=n=%ddB:d=%s" % (ruido_db, silencio_s),
              "-map", "0:v", "-f", "null", "-"])
    blocos, ini = [], None
    for ln in r.stderr.splitlines():
        m = re.search(r"freeze_start:\s*([\d.]+)", ln)
        if m:
            ini = float(m.group(1))
        m = re.search(r"freeze_end:\s*([\d.]+)", ln)
        if m and ini is not None:
            blocos.append((ini, float(m.group(1))))
            ini = None
    m = re.search(r"freeze_duration:\s*([\d.]+)", r.stderr)
    if ini is not None and m:
        blocos.append((ini, ini + float(m.group(1))))
    return blocos


def analisar(pasta, padrao="*.mp4"):
    pasta = Path(pasta)
    clipes = sorted(pasta.glob(padrao))
    plano = []
    print("%-38s %6s %8s %8s  %s" % ("clipe", "dur", "media", "pico", "ar morto"))
    for c in clipes:
        d = duracao(c)
        med, pk = nivel_audio(c)
        cong = ar_morto(c)
        total = sum(f - i for i, f in cong)
        print("%-38s %6.1f %8s %8s  %.1fs em %d trecho(s) %s"
              % (c.name[:38], d,
                 "?" if med is None else "%.1f" % med,
                 "?" if pk is None else "%.1f" % pk,
                 total, len(cong),
                 ["%.1f-%.1f" % b for b in cong][:3]))
        plano.append({"arquivo": str(c), "dur": d, "media_db": med, "pico_db": pk,
                      "congelado": cong, "congelado_s": round(total, 2)})
    return plano


def _filtro_clipe(c, idx, margem_morta=0.35, punch=True, cortar_meio=False, meio_min=1.5):
    """Plano do clipe: corta rabo morto, ar morto do gancho e (opcional) blocos
    mortos no MEIO; punch-in de 1,25x no meio do tempo restante.

    Zona protegida: ultimo quartil do clipe (a reacao SECA parada e comedia,
    nao lixo — LEI DO AR MORTO corta o tempo morto, nao o beat seco).
    Retorna (args_ffmpeg, dur_final_s). Modos:
      1 segmento sem punch -> "-vf" (comportamento antigo)
      1 segmento com punch -> grafo trim/trim (comportamento antigo, audio cru)
      n segmentos          -> grafo video+audio sincronizados (novo)
    """
    d = duracao(c)
    cong = ar_morto(c)
    corte_fim = d
    for ini, fim in cong:
        # se o congelamento encosta no fim (ou passa de 60% da duracao), corta ali
        if fim >= d - 0.15 and ini > d * 0.35:
            corte_fim = min(corte_fim, ini + margem_morta)
    corte_fim = max(corte_fim, 3.0)

    segs = []
    seg_ini = 0.0
    for ini, fim in sorted(cong):
        if ini <= 0.35 and fim <= d * 0.5:
            # ar morto no GANCHO (0-1s): a entrada nao pode ser parada
            seg_ini = max(seg_ini, min(fim - margem_morta, d * 0.3))
        elif cortar_meio and fim < corte_fim - 0.15 and (fim - ini) >= meio_min \
                and fim <= d * 0.75:
            # bloco morto no meio: remove com 0,25s de respiro antes do corte
            if ini - 0.25 - seg_ini >= 0.8:
                segs.append((seg_ini, ini - 0.25))
            seg_ini = fim + 0.05
    segs.append((seg_ini, corte_fim))
    segs = [(a, b) for a, b in segs if b - a >= 0.8]
    if not segs:
        segs = [(0.0, corte_fim)]
    dur_final = sum(b - a for a, b in segs)
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11,"
          "highpass=f=60,acompressor=threshold=-18dB:ratio=3:attack=8:release=180")

    if len(segs) == 1 and punch:
        a0, b0 = segs[0]
        meio = dur_final / 2.0
        graph = ("[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS[full];"
                 "[full]split[t1][t2];"
                 "[t1]trim=0:%.3f,setpts=PTS-STARTPTS[v1];"
                 "[t2]trim=start=%.3f,setpts=PTS-STARTPTS,"
                 "scale=iw*1.25:ih*1.25,crop=iw/1.25:ih/1.25[v2];"
                 "[v1][v2]concat=n=2:v=1:a=0[vout]" % (a0, b0, meio, meio))
        return (["-filter_complex", graph, "-map", "[vout]", "-map", "0:a",
                 "-af", "atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS," % (a0, b0) + af],
                dur_final)
    if len(segs) == 1:
        a0, b0 = segs[0]
        return (["-vf", "trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS" % (a0, b0),
                 "-af", "atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS," % (a0, b0) + af],
                dur_final)

    # n segmentos: video e audio cortados nos MESMOS pontos (sem dessincronia)
    pv = ["[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS[s%d]" % (a, b, i)
          for i, (a, b) in enumerate(segs)]
    pa = ["[0:a]atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS[a%d]" % (a, b, i)
          for i, (a, b) in enumerate(segs)]
    n = len(segs)
    graph = (";".join(pv) + ";" + "".join("[s%d]" % i for i in range(n))
             + "concat=n=%d:v=1:a=0[full];" % n)
    if punch:
        meio = dur_final / 2.0
        graph += ("[full]split[t1][t2];"
                  "[t1]trim=0:%.3f,setpts=PTS-STARTPTS[v1];"
                  "[t2]trim=start=%.3f,setpts=PTS-STARTPTS,"
                  "scale=iw*1.25:ih*1.25,crop=iw/1.25:ih/1.25[v2];"
                  "[v1][v2]concat=n=2:v=1:a=0[vout];" % (meio, meio))
    else:
        graph += "[full]null[vout];"
    graph += (";".join(pa) + ";" + "".join("[a%d]" % i for i in range(n))
              + "concat=n=%d:v=0:a=1[a0];[a0]" % n + af + "[aout]")
    return (["-filter_complex", graph, "-map", "[vout]", "-map", "[aout]"], dur_final)


def montar(pasta, saida, musica=None, dry=False, padrao="*.mp4",
           cortar_meio=False, meio_min=1.5):
    pasta = Path(pasta)
    clipes = sorted(pasta.glob(padrao))
    if not clipes:
        print("nenhum mp4 em", pasta)
        return 1

    tmp = pasta / "_pos"
    tmp.mkdir(exist_ok=True)
    preparados = []
    for i, c in enumerate(clipes, 1):
        espec, dur = _filtro_clipe(c, i, cortar_meio=cortar_meio, meio_min=meio_min)
        out = tmp / ("p%02d.mp4" % i)
        base = [FFMPEG, "-y", "-i", str(c)] + espec
        r = _run(base + ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
                         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)])
        print("[%d/%d] %s -> %.1fs %s" % (i, len(clipes), c.name, dur,
                                          "ok" if out.exists() else r.stderr[-200:]))
        preparados.append(out)
    if dry:
        print("\n--dry: clipes preparados em", tmp, "- sem concatenar")
        return 0

    lista = tmp / "lista.txt"
    lista.write_text("".join("file '%s'\n" % p for p in preparados), encoding="utf-8")
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lista)]
    if musica:
        cmd += ["-i", str(musica), "-filter_complex",
                "[1:a]volume=-26dB,aloop=loop=-1:size=2e9[m];[0:a][m]amix=inputs=2:"
                "duration=first:dropout_transition=0[a]", "-map", "0:v", "-map", "[a]"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(saida)]
    r = _run(cmd)
    if Path(saida).exists():
        med, pk = nivel_audio(saida)
        print("\nFINAL: %s · %.1fs · %s · media %s dB / pico %s dB"
              % (saida, duracao(saida), "%.1f MB" % (Path(saida).stat().st_size / 1e6),
                 "?" if med is None else "%.1f" % med, "?" if pk is None else "%.1f" % pk))
        return 0
    print("falhou:", r.stderr[-600:])
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta")
    ap.add_argument("--saida")
    ap.add_argument("--musica")
    ap.add_argument("--analisar", metavar="PASTA")
    ap.add_argument("--padrao", default="*.mp4", help="filtro de arquivos (ex: operacao_ralo_exato_v4_*.mp4)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--cortar-meio", action="store_true",
                    help="remove blocos mortos no MEIO do clipe (protege o ultimo "
                         "quartil = beat seco)")
    ap.add_argument("--meio-min", type=float, default=1.5,
                    help="duracao minima (s) de bloco morto removivel no meio")
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.analisar:
        plano = analisar(a.analisar, a.padrao)
        if a.json:
            Path(a.json).write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    if not (a.pasta and a.saida):
        ap.print_help()
        return 2
    return montar(a.pasta, a.saida, a.musica, a.dry, a.padrao,
                  cortar_meio=a.cortar_meio, meio_min=a.meio_min)


if __name__ == "__main__":
    sys.exit(main())
