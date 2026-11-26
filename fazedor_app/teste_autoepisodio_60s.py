# -*- coding: utf-8 -*-
"""teste_autoepisodio_60s.py — SORTEIA um tema na matriz e gera o episódio pelo MOTOR REAL.

Replica o fluxo do botao "🎲 Autoepisódio" da UI (ui.html):
  1. GET /api/pieces  -> dossie_md + comedia_canon + matriz (mesmo pacote da lapidarComAPI);
  2. sorteia tema (setor x servico x cliente x degrau x mecanismo + molde de abertura);
  3. POST /api/gerar  -> AgentRouter (kind=responses; chave SEMPRE do config_secret);
  4. POST /api/validar -> tem que sair com 0 erros (o canon v5 e cobrado);
  5. POST /api/salvar -> grava EPISODIOS/<slug>/episodio.json (recusa com erro);
  6. POST /api/settings -> settings/*.json com prompt v4 (steps 8 no template);
  7. grava EPISODIOS/_smoke_meta.json para a cadeia de render (smoke_60s.py).

Uso: python teste_autoepisodio_60s.py
Chaves NUNCA sao impressas.
"""
import json
import random
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8756"
APP = Path(__file__).resolve().parent
EPISODIOS = APP / "EPISODIOS"
META = EPISODIOS / "_smoke_meta.json"


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


def normaliza(t):
    return re.sub(r"\b(theo|teo|teó)\b", "TÉO", t, flags=re.I)
    # JUCA ja vem correto da matriz


def sorteia_tema(matriz):
    pick = lambda a: a[random.randrange(len(a))]          # noqa: E731
    setor = pick(matriz["setor"])
    servico = pick(matriz["servico"])
    cliente = pick(matriz["cliente"])
    degrau = pick(matriz["degrau"])
    mecanismo = pick(matriz["mecanismo"])
    molde = pick(["A", "B", "C"])
    abertura = {"A": "o cliente não aparece - eles chegam sozinhos ao local, carregando tudo",
                "B": "dois clientes discordam um do outro sobre como o serviço deve ficar",
                "C": "o prazo é curtíssimo e é anunciado por gestos apressados"}[molde]
    ideia = (f"Contratados para um serviço de {servico} num lugar do tipo {setor}, "
             f"para um cliente {cliente}. "
             f"Abertura: {abertura}. "
             f'O erro central nasce porque "{mecanismo}", e a escalada termina quando '
             f"tudo {degrau} (dano só material). "
             f"TÉO mede e planeja à esquerda; JUCA executa com confiança total à direita; "
             f"ninguém percebe nada. "
             f"Formato: episódio de 60 segundos = EXATAMENTE 6 clipes de 10 segundos "
             f"(estágios LIGACAO, CHEGADA, PRIMEIRA_FALHA, JEITINHO, ESCALADA, CLIMAX). "
             f"NÃO são 30 clipes.")
    resumo = (f"{servico.upper()} · {setor.upper()} · cliente {cliente.upper()} · "
              f'"{mecanismo}" → {degrau.upper()} (molde {molde})')
    return {"ideia": ideia, "resumo": resumo,
            "tema": {"setor": setor, "servico": servico, "cliente": cliente,
                     "degrau": degrau, "mecanismo": mecanismo, "molde": molde}}


def campos_canon(ep):
    """Checagem direta dos campos do cérebro de comédia (v5)."""
    faltando = [c for c in ("canon", "premissa_simples", "solucao_errada",
                            "escalada", "payoff_visual", "otimismo_final")
                if not str(ep.get(c, "")).strip()]
    por_clipe = []
    for s in ep.get("shots") or []:
        f = [c for c in ("causa", "efeito", "payoff", "escala")
             if not str(s.get(c, "")).strip()]
        por_clipe.append((s.get("n", "?"), f))
    return faltando, por_clipe


def gerar(pieces, fcfg, mensagens):
    api = {"kind": "responses", "endpoint": fcfg["ar_endpoint"], "model": fcfg["model_ar"]}
    print(">>> chamando o motor (AgentRouter %s) - 5 a 15 min..." % fcfg["model_ar"], flush=True)
    st, j = _post("/api/gerar", {"api": api, "messages": mensagens})
    if st != 200 or not j.get("episodio"):
        raise RuntimeError("gerar falhou (HTTP %s): %s" % (st, str(j)[:400]))
    return j


def mensagens_iniciais(pieces, ideia):
    v6 = pieces.get("v6") or ""          # v6 já traz o cérebro embutido
    base = v6 or pieces.get("dossie_md") or pieces.get("sistema") or ""
    extra = "" if v6 else ("\n\n" + (pieces.get("comedia_canon") or ""))
    return [
        {"role": "system", "content": base + extra},
        {"role": "user",
         "content": ("IDEIA DO USUÁRIO:\n" + ideia +
                     "\n\nResponda com RESUMO (máx 8 linhas, PT) + um único bloco "
                     "```json``` no formato PROMPT_MESTRE_V6 (planos/estado/som/música). "
                     "Nada depois do JSON.")},
    ]


def avaliar(ep):
    """Valida no motor. Devolve (ok, val, erros_em_texto, avisos_por_clipe)."""
    st, val = _post("/api/validar", {"episodio": ep})
    if st != 200:
        print("  (!) /api/validar HTTP %s: %s" % (st, str(val)[:300]), flush=True)
        return False, val, ["validador travou com o JSON enviado: %s" % str(val)[:300]], []
    print("VALIDACAO: nota %s/10 (humor %s · render %s · montage %s)"
          % (val.get("nota"), val.get("humor"), val.get("render"), val.get("montage")))
    for c in (val.get("checks_montage") or [])[:14]:
        print("  ok -", c)
    for a in (val.get("avisos") or []):
        print("  AVISO:", str(a)[:150])
    for e in (val.get("erros") or []):
        print("  ERRO:", str(e)[:150])
    faltando, por_clipe = campos_canon(ep)
    print("CANON v5: campos de episodio faltando = %s | clipes incompletos = %s"
          % (faltando or "NENHUM", [c for c, f in por_clipe if f] or "NENHUM"))
    erros = [str(x) for x in (val.get("erros") or [])]
    avisos_clipe = [str(a) for a in (val.get("avisos") or [])
                    if str(a).startswith("[") and ("parado" in str(a)
                                                   or "palavras" in str(a)
                                                   or "verbo físico" in str(a)
                                                   or "evento(s) de som" in str(a))]
    return (not erros), val, erros, avisos_clipe


def main():
    pieces = _get("/api/pieces")
    fcfg = _get("/api/fcfg")
    if not fcfg.get("ar_key"):
        raise SystemExit("sem chave AgentRouter no config_secret.json")
    tema = sorteia_tema(pieces.get("matriz") or {})
    print("=" * 78)
    print("TEMA SORTEADO:", tema["resumo"])
    print("=" * 78)

    mensagens = mensagens_iniciais(pieces, normaliza(tema["ideia"]))
    episodio = None
    cru = None
    for rodada in (1, 2, 3, 4):
        j = gerar(pieces, fcfg, mensagens)
        (EPISODIOS / "_ultima_geracao.json").write_text(
            json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        cru = j.get("cru") or ""
        ep = j["episodio"]
        n = len(ep.get("shots") or [])
        print("\nRESUMO DA IA:\n%s" % (j.get("resumo") or "")[:1200])
        print("\n>>> episodio: %s | %d clipes | rodada %d" % (ep.get("titulo"), n, rodada))
        ok, val, erros, av_clipe = avaliar(ep)
        (EPISODIOS / "_ultima_validacao.json").write_text(
            json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")
        if ok and n == 6:
            episodio = ep
            break
        print("\n--- rodada %d nao serviu (erros=%d, clipes=%d) - CORRECAO via historico ---"
              % (rodada, len(erros), n), flush=True)
        lista = "\n".join("%d. %s" % (i + 1, e) for i, e in enumerate(erros[:14])) or \
            "- o JSON deve ter EXATAMENTE 6 objetos em shots (c01..c06), cada um com dur 10"
        if av_clipe:
            lista += "\n\nAjuste tambem (avisos que viram defeito no video):\n" + \
                     "\n".join("- " + a for a in av_clipe[:8])
        mensagens = mensagens + [
            {"role": "assistant", "content": cru[:60000]},
            {"role": "user",
             "content": ("Seu JSON anterior falhou na validação do pipeline. Devolva O JSON "
                         "COMPLETO corrigido (mesmo formato: RESUMO curto + um único bloco "
                         "```json```), corrigindo:\n" + lista +
                         "\nLembre: 6 clipes de 10 s (LIGACAO, CHEGADA, PRIMEIRA_FALHA, "
                         "JEITINHO, ESCALADA, CLIMAX); TODO objeto_gag entra em "
                         "objetos_plantados (plantado_no_clipe = primeiro clipe em que "
                         "aparece, pago_no_clipe = o último); herda_de = NOME CURTO verbatim "
                         "do estado_out/objeto_gag do clipe anterior (nunca uma frase); "
                         "a MESMA família de objeto_gag volta em 2+ clipes com física "
                         "diferente (arco); gag com verbo físico na 1a frase do action; "
                         "nada de 'precisely'; action 35-70 palavras com os dois corpos "
                         "agitando; som com 4-6 eventos nomeados + 1 som não-verbal; "
                         "gesto-assinatura no máximo 3x no episódio inteiro.")},
        ]

    if episodio is None:
        raise SystemExit("XX autoepisodio nao ficou valido em 4 rodadas (1 + 3 correções)")

    st, salvo = _post("/api/salvar", {"episodio": episodio})
    if st not in (201, 202):
        raise SystemExit("XX salvar recusou (HTTP %s): %s" % (st, str(salvo)[:400]))
    slug = salvo.get("slug") or salvo.get("nome") or Path(salvo.get("pasta") or "").name
    pasta = salvo.get("pasta") or ""
    print(">>> SALVO: %s (%s)" % (slug, pasta))
    destino = Path(pasta)
    if destino.exists():
        destino.joinpath("geracao_v6.json").write_text(
            json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        destino.joinpath("validacao_v6.json").write_text(
            json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")
        print(">>> respostas brutas salvas: geracao_v6.json + validacao_v6.json", flush=True)

    st, cfgs = _post("/api/settings", {"episodio": episodio})
    if st != 201:
        raise SystemExit("XX settings falhou (HTTP %s): %s" % (st, str(cfgs)[:400]))
    print(">>> SETTINGS gerados (total %s s)" % cfgs.get("total_s"))

    META.write_text(json.dumps({"slug": slug, "pasta": pasta, "tema": tema["tema"],
                                "resumo": tema["resumo"], "ideia": tema["ideia"]},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(">>> meta para a cadeia: %s" % META)
    print("\n>>> TESTE DO MOTOR OK — episódio válido com o cérebro de comédia v5.")


if __name__ == "__main__":
    main()
