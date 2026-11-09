# -*- coding: utf-8 -*-
"""RENDER DE FUMAÇA — roda os N primeiros clipes de um episódio salvo e concatena.
Uso:  python render_fumaca.py [slug] [n_clipes=3]
Sem slug: usa o episódio mais recente de EPISODIOS."""
import json, io, os, subprocess, sys, time, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
import fazedor_app as F          # reusa PYTHON_GEN / GEN_TEST / DIR_GEN_TEST / EPISODIOS_DIR

N = int(sys.argv[2]) if len(sys.argv) > 2 else 3

# episódio: por slug ou o mais recente
if len(sys.argv) > 1:
    pasta = F.EPISODIOS_DIR / sys.argv[1]
else:
    pastas = sorted([d for d in F.EPISODIOS_DIR.iterdir() if d.is_dir()],
                    key=lambda d: d.stat().st_mtime, reverse=True)
    pasta = pastas[0]
slug = pasta.name
sdir = pasta / "settings"
settings = sorted(sdir.glob("*.json"))[:N]
if not settings:
    print(f"SEM settings em {sdir} — clique ⚙️ Settings v2.1 no app primeiro")
    sys.exit(2)

print(f"=== FUMAÇA: {slug} · clipes {[p.stem.split('_c')[1][:2] for p in settings]} ===")
print(f"gen_test: {F.GEN_TEST}")
print(f"python:   {F.PYTHON_GEN}\n")

mp4s = []
for i, arq in enumerate(settings, 1):
    nome = arq.stem                       # <slug>_cNN_<estagio>_settings
    tag = f"{slug}_FUMACA_{i:02d}"
    t0 = time.time()
    antes = time.time()
    r = subprocess.run([F.PYTHON_GEN, F.GEN_TEST, "--settings", str(arq), "--tag", tag],
                       cwd=str(F.DIR_GEN_TEST), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=7200)
    dur = time.time() - t0
    # localiza o mp4 gerado: procura no gen_test E na pasta outputs do WanGP
    raizes = [Path(F.DIR_GEN_TEST), Path(r"C:\pinokio\api\wan2gp-amd\app\outputs")]
    cand = []
    for raiz in raizes:
        cand += [p for p in glob.glob(str(raiz / "**" / "*.mp4"), recursive=True)
                 if os.path.getmtime(p) >= antes - 5]
    cand.sort(key=os.path.getmtime, reverse=True)
    mp4 = cand[0] if cand else None
    if mp4:
        mp4s.append(mp4)
    print(f"[{i}/{len(settings)}] {nome}")
    print(f"  tempo: {dur/60:.1f} min ({dur:.0f}s) · rc={r.returncode} · mp4={Path(mp4).name if mp4 else 'NÃO ACHOU'}")
    if r.returncode != 0:
        print("  STDERR (últimas 12 linhas):")
        for ln in (r.stderr or "").strip().splitlines()[-12:]:
            print("   ", ln[:170])
        if not mp4:
            print("  FALHOU — abortando os próximos")
            break

if not mp4s:
    print("\nNenhum clipe gerado — ver o STDERR acima")
    sys.exit(1)

# concatena
lista = pasta / "fumaca_lista.txt"
lista.write_text("\n".join(f"file '{m}'" for m in mp4s), encoding="utf-8")
final = pasta / f"{slug}_fumaca_{len(mp4s)}clipes.mp4"
fc = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                     "-c", "copy", str(final)], capture_output=True, text=True)
print(f"\n=== FUMAÇA CONCLUÍDA ===")
print(f"clipes: {len(mp4s)} · final: {final}")
print(f"tamanho: {(final.stat().st_size/1e6):.1f} MB" if final.exists() else "concat falhou: " + (fc.stderr or "")[-300:])
