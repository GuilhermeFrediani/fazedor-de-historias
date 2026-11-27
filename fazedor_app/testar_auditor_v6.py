# -*- coding: utf-8 -*-
"""testar_auditor_v6.py — auditoria cruzada do episódio recém-gerado.

Criação: gpt-6.2-astra (usado por teste_autoepisodio_60s.py).
Auditoria: o OUTRO modelo (gpt-6.2-sol), escolhido por /api/auditar quando
modelo_criador = gpt-6.2-astra.

Uso: python testar_auditor_v6.py
Chaves NUNCA são impressas.
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8756"
APP = Path(__file__).resolve().parent
META = APP / "EPISODIOS" / "_smoke_meta.json"


def _get(caminho):
    with urllib.request.urlopen(BASE + caminho, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(caminho, corpo, timeout=1800):
    ped = urllib.request.Request(BASE + caminho, data=json.dumps(corpo).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(ped, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", default="", help="pasta do episódio (default: _smoke_meta.json)")
    a = ap.parse_args()
    if a.pasta:
        pasta = Path(a.pasta)
    else:
        m = json.loads(META.read_text(encoding="utf-8"))
        pasta = Path(m["pasta"])
    episodio = json.loads((pasta / "episodio.json").read_text(encoding="utf-8"))
    fcfg = _get("/api/fcfg")
    criador = fcfg["model_ar"]

    # NAO fabricamos state_ledger: um ledger com posicoes fixas e consequencias
    # vazias induz o auditor a erro de continuidade e esconde o ledger real do
    # episodio (mensagem_usuario() so usa o episodio quando NAO vem ledger).
    corpo = {
        "api": {"kind": "responses", "endpoint": fcfg["ar_endpoint"], "model": criador},
        "episodio": episodio,
        "modelo_criador": criador,
    }
    print("=" * 78)
    print("AUDITORIA CRUZADA | criador=%s -> auditor=%s (o outro modelo)"
          % (criador, "gpt-6.2-sol"), flush=True)
    print("episódio:", episodio.get("titulo"), "| clipes:", len(episodio.get("shots") or []),
          flush=True)
    print(">>> chamando /api/auditar (5-15 min)...", flush=True)

    st, j = _post("/api/auditar", corpo)
    if st != 200 or "relatorio" not in j:
        raise SystemExit("auditar falhou (HTTP %s): %s" % (st, str(j)[:600]))

    destino = pasta / "auditoria_v6.json"
    destino.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
    print(">>> bruto salvo:", destino, flush=True)
    print("MODELO AUDITOR:", j.get("modelo"), "| uso:", j.get("uso"), flush=True)

    r = j["relatorio"]
    a = r.get("auditoria") or {}
    print("\nSTATUS:", a.get("status"), "| nota geral:", a.get("nota_geral"))
    print("NOTAS:", a.get("notas"))
    print("FALHAS: criticas=%s altas=%s medias=%s baixas=%s" %
          (a.get("falhas_criticas"), a.get("falhas_altas"),
           a.get("falhas_medias"), a.get("falhas_baixas")))
    cam = a.get("camadas") or {}
    if cam:
        print("CAMADAS:", {k: v.get("status") for k, v in cam.items()
                           if isinstance(v, dict)})
    for p in (r.get("problemas") or []):
        print("\n  [clipe %s] %s / %s: %s" %
              (p.get("clipe"), p.get("severidade"), p.get("campo"),
               p.get("problema")))
        print("    evidência:", str(p.get("evidencia", ""))[:300])
        print("    correção:", str(p.get("correcao_sugerida", ""))[:300])
        print("    dependentes:", p.get("campos_dependentes"))
    for c in (r.get("correcoes") or []):
        print("\n  CORREÇÃO clipe %s / %s: %s" %
              (c.get("clipe"), c.get("campo"), str(c.get("valor_corrigido", ""))[:300]))
    print("\nRESUMO:", r.get("resumo"))
    print("\n>>> AUDITORIA CRUZADA CONCLUIDA", flush=True)


if __name__ == "__main__":
    main()
