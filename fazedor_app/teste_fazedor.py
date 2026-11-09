#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste local do Fazedor de Histórias: sobe o servidor numa porta livre,
bate nas rotas com o episódio exemplo, grava settings e lê de volta —
e apaga os artefatos de teste no fim.  python teste_fazedor.py"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parent
PY = sys.executable

def ok(nome, cond, extra=""):
    print(("PASSOU " if cond else "FALHOU ") + nome + (f"  · {extra}" if extra else ""))
    return bool(cond)

def porta():
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        return sk.getsockname()[1]

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def post(url, obj):
    ped = urllib.request.Request(url, data=json.dumps(obj).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(ped, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def main():
    porta_s = porta()
    srv = subprocess.Popen([PY, "fazedor_app.py"], cwd=APP,
                           env={**__import__("os").environ, "PORTA": str(porta_s), "SEM_BROWSER": "1"})
    base = f"http://127.0.0.1:{porta_s}"
    tudo_ok = True
    try:
        time.sleep(2.5)
        import os

        pz = get(base + "/api/pieces")
        tudo_ok &= ok("bases /api/pieces", len(pz["sistema"]) > 5000 and "JUCA" in pz["exemplo"])

        r = urllib.request.urlopen(base + "/")
        html = r.read().decode("utf-8")
        tudo_ok &= ok("UI servida", "FAZEDOR DE HISTÓRIAS" in html and "SpeechRecognition" in html)

        ep = json.loads((APP.parent / "exemplo_episodio_pintura.json").read_text(encoding="utf-8"))
        st, v = post(base + "/api/validar", {"episodio": ep})
        tudo_ok &= ok("validar exemplo", st == 200 and len(v["erros"]) == 0,
                      f"{len(v['erros'])} erros · {len(v['avisos'])} avisos · {v['total_s']}s")
        for av in v.get("avisos", []):
            print("        aviso:", av)

        st, s = post(base + "/api/salvar", {"episodio": ep})
        tudo_ok &= ok("salvar", st == 201 and Path(s["pasta"], "episodio.json").exists())
        n_shots = len(list(Path(s["pasta"]).glob("shot_*.txt")))
        tudo_ok &= ok("shot_NN.txt gravados", n_shots == len(ep["shots"]), f"{n_shots} arquivos")

        st, g = post(base + "/api/settings", {"episodio": ep})
        tudo_ok &= ok("settings gerados", st == 201 and Path(g["settings_dir"]).exists(),
                      f"est {g['horas_estimadas']}h @80s/s")
        primeiro = Path(g["arquivos"][0])
        cfg = json.loads(primeiro.read_text(encoding="utf-8"))
        chaves_necessarias = ["model_type", "num_inference_steps", "resolution", "force_fps",
                              "video_length", "seed", "guidance_scale", "flow_shift",
                              "skip_steps_cache_type", "audio_prompt_type", "activated_loras",
                              "loras_multipliers", "output_filename", "config", "_cli_extra", "prompt"]
        tudo_ok &= ok("settings formato v2.1", all(c in cfg for c in chaves_necessarias)
                      and cfg["seed"] == 7001 and cfg["num_inference_steps"] == 6
                      and "turbo" in cfg["activated_loras"][0]
                      and len(cfg["prompt"]) in range(2000, 7100),
                      f"{len(cfg['prompt'])} chars no prompt")
        tudo_ok &= ok("corrente .ps1", Path(g["corrente"]).exists()
                      and "gen_test.py" in Path(g["corrente"]).read_text(encoding="utf-8"))

        # lista e sobreposição
        st2, ep2 = post(base + "/api/salvar", {"episodio": ep})
        tudo_ok &= ok("recusa sobrescrever", st2 == 409, str(ep2.get("erro", ""))[:60])
        ls = get(base + "/api/episodios")
        tudo_ok &= ok("lista", any(e["nome"] == Path(s["pasta"]).name for e in ls["episodios"]))
    finally:
        srv.terminate()
        time.sleep(1.0)
        destino = APP / "EPISODIOS" / "fachada-em-dois-tons"
        if destino.exists():
            import shutil
            shutil.rmtree(destino)
            try:
                (APP / "EPISODIOS").rmdir()
            except OSError:
                pass
        print("limpeza: pasta de teste removida")
    print("\n== RESULTADO:", "TUDO OK" if tudo_ok else "HOUVE FALHAS", "==")
    sys.exit(0 if tudo_ok else 1)

if __name__ == "__main__":
    main()
