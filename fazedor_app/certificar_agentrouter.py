# -*- coding: utf-8 -*-
"""CERTIFICADOR AGENTROUTER — prova que os 3 modelos conhecem o pipeline.

Para cada modelo (gpt-6.1-sol, gpt-6-astra, gpt-5.6-sol):
  1. monta o historico EXATAMENTE como a UI (sistema 14 regras + exemplo + ideia)
  2. POST /api/gerar (rota real do app → kind responses → /v1/responses)
  3. POST /api/validar (as 14 regras do montar_prompts.py)
  4. se houver erros → rodada de correção (como o botão 🧠 corrigir) → revalida
Veredito por modelo. Rodar com o servidor ligado (python fazedor_app.py).
"""
import json, io, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8756"
AR_ENDPOINT = "https://agentrouter.org/v1/responses"
MODELOS = ("gpt-6.1-sol", "gpt-6-astra", "gpt-5.6-sol")
if len(sys.argv) > 1:                      # ex.: python certificar_agentrouter.py gpt-6.1-sol
    MODELOS = tuple(sys.argv[1:])
CF = "```"
IDEIA = ("Contratados para tirar as cracas do casco de um navio encalhado na praia. "
         "Juca tenta arrancar as cracas na marra e Teo inventa uma máquina com o "
         "bote salva-vidas. Cada tentativa cria um caos novo.")


def pega(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def post(url, obj, timeout=3600):
    ped = urllib.request.Request(url, data=json.dumps(obj).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(ped, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def historico(sistema, exemplo, ideia):
    """Dossiê v1.0: MEMORY DIRECTIVE como system + ideia. Sem exemplo (o template
    já está dentro da directive; o exemplo antigo é de outro formato)."""
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": "IDEIA DO USUÁRIO:\n" + ideia +
                                    "\n\nResponda com RESUMO (máx 8 linhas, PT) + um único bloco "
                                    + CF + "json" + CF + " no TEMPLATE DE SAÍDA da MEMORY DIRECTIVE. "
                                    "Nada depois do JSON."},
    ]


def valida(ep):
    return post(BASE + "/api/validar", {"episodio": ep})


def certifica(modelo, api, hist):
    t0 = time.time()
    j = post(BASE + "/api/gerar", {"api": api, "messages": hist})
    cru, ep = j.get("cru", ""), j.get("episodio")
    tokens1 = (j.get("uso") or {}).get("total_tokens")
    if not isinstance(ep, dict) or not ep.get("shots"):
        return {"modelo": modelo, "ok": False, "fase": "JSON não extraído da resposta",
                "detalhe": cru[:300], "s": time.time() - t0, "tokens": tokens1}
    v = valida(ep)
    erros, avisos = list(v.get("erros") or []), list(v.get("avisos") or [])
    rodadas = 1
    if erros:   # rodada de correção (como o botão 🧠)
        msg = ("Seu JSON anterior falhou na validação do pipeline. Devolva O JSON COMPLETO "
               "corrigido (mesmo formato: RESUMO curto + um único bloco " + CF + "json" + CF +
               "), corrigindo:\n" + "\n".join(f"{i+1}. {e}" for i, e in enumerate(erros)))
        hist2 = hist + [{"role": "assistant", "content": cru},
                        {"role": "user", "content": msg}]
        t1 = time.time()
        j2 = post(BASE + "/api/gerar", {"api": api, "messages": hist2})
        cru2, ep2 = j2.get("cru", ""), j2.get("episodio")
        rodadas, t0b = 2, time.time() - t1
        if isinstance(ep2, dict) and ep2.get("shots"):
            v2 = valida(ep2)
            erros2, avisos2 = list(v2.get("erros") or []), list(v2.get("avisos") or [])
            if len(erros2) <= len(erros):
                cru, ep, erros, avisos, tokens1 = (cru2, ep2, erros2, avisos2,
                                                   (tokens1 or 0) + ((j2.get("uso") or {}).get("total_tokens") or 0))
    return {"modelo": modelo, "ok": not erros, "erros": erros, "avisos": avisos,
            "rodadas": rodadas, "shots": len((ep or {}).get("shots") or []),
            "tokens": tokens1, "s": time.time() - t0}


if __name__ == "__main__":
    print("== CERTIFICADOR AGENTROUTER — pipeline TÉO & JUCA ==")
    p = pega(BASE + "/api/pieces")
    print(f"bases: dossie_md {len(p.get('dossie_md',''))} chars · sistema(legado) {len(p['sistema'])} chars · "
          f"blocos {len(p['blocos']) if isinstance(p['blocos'], dict) else '?'} chaves")
    key = pega(BASE + "/api/fcfg").get("ar_key", "")
    if not key:
        print("SEM agentrouter_key em config_secret.json — abortando")
        sys.exit(2)
    hist = historico(p.get("dossie_md") or p["sistema"], p["exemplo"], IDEIA)
    print(f"ideia: {IDEIA}\n")
    placar = {}
    for m in MODELOS:
        api = {"kind": "responses", "endpoint": AR_ENDPOINT, "key": key, "model": m,
               "temperature": 0.8, "max_tokens": 16000, "na_fallback": True}
        print(f"--- {m} ---")
        try:
            r = certifica(m, api, hist)
        except Exception as e:
            r = {"modelo": m, "ok": False, "fase": "exceção", "detalhe": str(e)[:300], "s": 0}
        if r.get("ok"):
            ver = "APROVADO (0 erros)"
        elif "erros" in r:
            ver = f"FALHOU ({len(r['erros'])} erros: {r['erros'][:2]})"
        else:
            ver = f"FALHOU ({r.get('fase')}: {str(r.get('detalhe'))[:160]})"
        placar[m] = ver
        print(f"  {time.strftime('%H:%M:%S')} · {r.get('s',0):5.1f}s · rodadas={r.get('rodadas',1)} "
              f"· shots={r.get('shots','?')} · tokens={r.get('tokens','?')}")
        print(f"  VEREDITO: {ver}")
        if r.get("avisos"):
            print(f"  avisos ({len(r['avisos'])}): {r['avisos'][:3]}")
        print()
    print("== PLACAR FINAL ==")
    for m, v in placar.items():
        print(f"  {m:<14} {v}")
