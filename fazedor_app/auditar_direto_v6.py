# -*- coding: utf-8 -*-
"""auditar_direto_v6.py — auditoria cruzada chamando o AgentRouter direto.

Evita depender do servidor HTTP (que pode estar ocupado com outro teste) e
usa o sistema do AUDITOR_V6 de verdade, não o prompt de roteirista.

Uso: python auditar_direto_v6.py "<pasta do episódio>"
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

import fazedor_app as app  # noqa: E402
import auditor_v6  # noqa: E402


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python auditar_direto_v6.py <pasta>")
    pasta = Path(sys.argv[1])
    ep = json.loads((pasta / "episodio.json").read_text(encoding="utf-8"))
    ledger = {"episode_state": {
        "objects": ep.get("objetos_plantados") or [],
        "character_positions": {"teo": "left", "juca": "right"},
        "persistent_consequences": [],
    }}
    mensagens = [
        {"role": "user", "content": auditor_v6.mensagem_usuario(ep, ledger)}
    ]
    key = app.ler_chave_agentrouter()
    if not key:
        raise SystemExit("sem chave AgentRouter")

    print("=" * 78)
    print("AUDITORIA DIRETA | criador=gpt-6.2-astra -> auditor=gpt-6.2-sol", flush=True)
    print("episódio:", ep.get("titulo"), "| clipes:", len(ep.get("shots") or []), flush=True)

    txt = None
    uso = None
    ultimo = None
    for orcamento, espera in zip((64000, 48000, 32000), (0, 10, 25)):
        if espera:
            time.sleep(espera)
        try:
            print(">>> chamando gpt-6.2-sol (orcamento %d)..." % orcamento, flush=True)
            txt, uso, rid = app.agentrouter_responses(
                key, "gpt-6.2-sol", mensagens, orcamento,
                sistema=auditor_v6.PROMPT_AUDITOR_V6)
            break
        except Exception as e:
            ultimo = "%s: %s" % (type(e).__name__, str(e)[:250])
            print("  falhou:", ultimo, flush=True)
    if txt is None:
        raise SystemExit("XX auditor falhou: " + str(ultimo))

    cru = pasta / "auditoria_cru_v6.txt"
    cru.write_text(txt, encoding="utf-8")
    print(">>> bruto salvo:", cru, "| uso:", uso, flush=True)

    resumo, rel = app.extrair_json(txt)
    if not isinstance(rel, dict) or "auditoria" not in rel:
        print("XX extrair_json nao conseguiu o relatorio", flush=True)
        print("RESUMO/INICIO:", (resumo or "")[:800], flush=True)
        print("CRU (2000):", txt[:2000], flush=True)
        raise SystemExit(2)

    (pasta / "auditoria_v6.json").write_text(
        json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    a = rel.get("auditoria") or {}
    print("\nSTATUS:", a.get("status"), "| nota geral:", a.get("nota_geral"))
    print("NOTAS:", a.get("notas"))
    print("FALHAS: criticas=%s altas=%s medias=%s baixas=%s" %
          (a.get("falhas_criticas"), a.get("falhas_altas"),
           a.get("falhas_medias"), a.get("falhas_baixas")))
    for p in (rel.get("problemas") or []):
        print("\n  [clipe %s] %s / %s: %s" %
              (p.get("clipe"), p.get("severidade"), p.get("campo"),
               p.get("problema")))
        print("    evidencia:", str(p.get("evidencia", ""))[:300])
        print("    correcao:", str(p.get("correcao_sugerida", ""))[:300])
        print("    dependentes:", p.get("campos_dependentes"))
    for c in (rel.get("correcoes") or []):
        print("\n  CORRECAO clipe %s / %s: %s" %
              (c.get("clipe"), c.get("campo"), str(c.get("valor_corrigido", ""))[:300]))
    print("\nRESUMO:", rel.get("resumo"))
    print("\n>>> AUDITORIA CONCLUIDA", flush=True)


if __name__ == "__main__":
    main()
