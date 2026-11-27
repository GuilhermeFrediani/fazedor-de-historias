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
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8756"
APP = Path(__file__).resolve().parent
EPISODIOS = APP / "EPISODIOS"
META = EPISODIOS / "_smoke_meta.json"
GATE = EPISODIOS / "_gate_v6.json"


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


# ─────────────────────────────────────────────────────────────────────────────
# GATE FINAL: auditoria independente (Sol) + correção do Astra
# ─────────────────────────────────────────────────────────────────────────────
def _reset_gate(motivo):
    """Uma história reprovada zera a sequência: o smoke exige 3 aprovadas seguidas."""
    try:
        GATE.write_text(json.dumps(
            {"consecutivas": 0, "historias": [], "reset_motivo": motivo,
             "quando": datetime.now().isoformat(timespec="seconds")},
            ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print("  (!) nao consegui gravar o gate:", e, flush=True)


def _registra_gate(slug, rel):
    try:
        g = json.loads(GATE.read_text(encoding="utf-8"))
    except Exception:
        g = {"consecutivas": 0, "historias": []}
    a = (rel.get("relatorio") or {}).get("auditoria") or {}
    g["historias"] = (g.get("historias") or [])[-2:] + [{
        "slug": slug,
        "status": a.get("status"),
        "nota_geral": a.get("nota_geral"),
        "causalidade": (a.get("notas") or {}).get("causalidade"),
        "criticas": a.get("falhas_criticas"),
        "altas": a.get("falhas_altas"),
        "quando": datetime.now().isoformat(timespec="seconds"),
    }]
    g["consecutivas"] = min(3, int(g.get("consecutivas", 0)) + 1)
    g.pop("reset_motivo", None)
    GATE.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
    return g


def auditar(ep, fcfg):
    """Chama /api/auditar (Sol). Exige relatório JSON válido; tenta 2x.

    NÃO inventamos state_ledger: um ledger com posições fixas (ex.: "teo":
    "left" sempre) induziria o auditor a marcar continuidade falsa quando o
    episódio move os personagens. O campo é opcional — o próprio episódio já
    carrega objetos_plantados/estado_in/estado_out, que é o que importa.
    """
    corpo = {
        "api": {"kind": "responses", "endpoint": fcfg["ar_endpoint"],
                "model": fcfg["model_ar"]},
        "episodio": ep,
        "modelo_criador": fcfg["model_ar"],
    }
    ultimo = ""
    for tent in (1, 2):
        print(">>> auditoria independente (Sol) - tentativa %d/2 (~3 min)..." % tent,
              flush=True)
        st, j = _post("/api/auditar", corpo, timeout=2400)
        if (st == 200 and isinstance(j.get("relatorio"), dict)
                and isinstance(j["relatorio"].get("auditoria"), dict)):
            return j
        ultimo = "HTTP %s: %s" % (st, str(j)[:400])
        print("  (!) auditoria invalida: %s" % ultimo, flush=True)
    raise RuntimeError("auditoria sem relatorio JSON valido (%s)" % ultimo)


def auditoria_aprovada(rel):
    """Critério do gate (calibrado 27/11 com o usuário).

    O Sol é o dono de CRITICAS e ALTAS de causalidade — médias e baixas são
    ajuste fino e não bloqueiam o render. O gate aceita:
      - status APROVADO ou CORRECAO_NECESSARIA;
      - zero críticas e zero altas (campos E lista de problemas);
      - causalidade >= 8;
      - as 3 camadas presentes e NENHUMA REPROVADO.
    """
    a = (rel.get("relatorio") or {}).get("auditoria") or {}
    notas = a.get("notas") or {}
    try:
        causalidade = float(notas.get("causalidade", 0) or 0)
    except Exception:
        causalidade = 0.0
    try:
        criticas = int(a.get("falhas_criticas", 1) or 0)
    except Exception:
        criticas = 1
    try:
        altas = int(a.get("falhas_altas", 1) or 0)
    except Exception:
        altas = 1
    probs = (rel.get("relatorio") or {}).get("problemas") or []
    severidades = [str(p.get("severidade", "")).upper() for p in probs]
    tem_critico = any(s.startswith("CRIT") for s in severidades)
    tem_alto = any(s.startswith("ALTO") for s in severidades)
    camadas = a.get("camadas") or {}
    # exige as 3 camadas reais: all() sobre dict vazio seria verdade por vacuidade
    # e liberaria o smoke sem o veredito por camada.
    esperadas = ("estrutural", "narrativa", "visual_fisica")
    chaves_ok = all(k in camadas for k in esperadas)
    nenhuma_reprovada = chaves_ok and all(
        str((camadas.get(k) or {}).get("status", "")).upper() != "REPROVADO"
        for k in esperadas)
    status = str(a.get("status", "")).upper()
    return (status in ("APROVADO", "CORRECAO_NECESSARIA") and causalidade >= 8.0
            and criticas == 0 and altas == 0 and not tem_critico and not tem_alto
            and nenhuma_reprovada)


def mensagem_correcao_auditoria(rel):
    r = rel.get("relatorio") or {}
    probs = r.get("problemas") or []
    linhas = []
    for p in probs[:14]:
        linhas.append("- clipe %s | %s | %s: %s | correcao: %s | dependentes: %s" % (
            p.get("clipe"), p.get("severidade"), p.get("campo"),
            str(p.get("problema", ""))[:400], str(p.get("correcao_sugerida", ""))[:400],
            p.get("campos_dependentes")))
    if not linhas:
        linhas = ["- o auditor reprovou sem lista; corrija causalidade/fisica pelo resumo."]
    return (
        "O AUDITOR INDEPENDENTE (SOL) REPROVOU este episodio. Corrija APENAS os "
        "problemas abaixo, sem reescrever o resto — preservar o render vale tanto "
        "quanto corrigir: a versao auditada ja passou no validador com render >= 7. "
        "Devolva O JSON COMPLETO no formato PROMPT_MESTRE_V6 (RESUMO curto + um unico "
        "bloco ```json```), com 6 clipes de 10 s.\n"
        "LEIS QUE A CORRECAO NAO PODE VIOLAR:\n"
        "- Continuidade: se mudar estado_out, ajuste estado_in do proximo; se mudar "
        "posicao/mao de objeto, ajuste o registro.\n"
        "- Transicao fisica: CONTATO -> transformacao -> resultado nos planos.\n"
        "- Dois corpos em acao fisica em TODOS os planos: quem nao executa interfere "
        "(empurra, segura, trava, corrige). PROIBIDO nos planos e reacoes: stays, "
        "waits, watches, stands by, looks on, observa, acompanha, espera — isso "
        "derruba a nota de render e reprova o episodio.\n"
        "- Som bucal MODERADO: no maximo 1 por clipe, em 2-5 dos 6 clipes — NUNCA em "
        "todos, NUNCA zero.\n"
        "- Nada de N/A na musica.\n\n"
        "PROBLEMAS DO AUDITOR:\n" + "\n".join(linhas) +
        "\n\nRESUMO DO AUDITOR: " + str(r.get("resumo", ""))[:1200])


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
                         "diferente (arco); gag/planos com verbo físico visível; "
                         "nada de 'precisely'; planos[1] com 20-95 palavras e os dois "
                         "corpos agitando; som com 4-6 eventos (material + evento), som "
                         "bucal opcional (no máximo 1, quando tiver função); "
                         "gesto-assinatura no máximo 3x no episódio inteiro.")},
        ]

    if episodio is None:
        _reset_gate("autoepisodio nao ficou valido em 4 rodadas")
        raise SystemExit("XX autoepisodio nao ficou valido em 4 rodadas (1 + 3 correções)")

    # ── GATE FINAL: auditoria independente (Sol) ─────────────────────────────
    print("\n" + "=" * 78)
    print(">>> AUDITORIA INDEPENDENTE (Sol) — o criador nao aprova o proprio trabalho")
    print("=" * 78, flush=True)
    rel = None
    aprovado = False
    a_rodada = 0
    for a_rodada in (1, 2, 3):
        try:
            rel = auditar(episodio, fcfg)
        except Exception as e:
            _reset_gate("auditoria indisponivel: %s" % str(e)[:200])
            raise SystemExit("XX auditoria indisponivel - settings/smoke NAO foram "
                             "gerados: %s" % e)
        (EPISODIOS / "_ultima_auditoria.json").write_text(
            json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
        a = (rel.get("relatorio") or {}).get("auditoria") or {}
        cam = a.get("camadas") or {}
        print("\nAUDITORIA %d: %s | nota %s | causalidade %s | criticas %s"
              % (a_rodada, a.get("status"), a.get("nota_geral"),
                 (a.get("notas") or {}).get("causalidade"), a.get("falhas_criticas")),
              flush=True)
        if cam:
            print("CAMADAS:", {k: (v or {}).get("status") for k, v in cam.items()
                               if isinstance(v, dict)}, flush=True)
        if auditoria_aprovada(rel):
            aprovado = True
            break
        # mostra os problemas SEMPRE (inclusive na ultima rodada, quando o loop
        # quebra — sem isso o veredito final fica sem diagnostico no log)
        print("\n--- auditoria REPROVOU (%s) ---"
              % ("ultima rodada" if a_rodada == 3 else "Astra corrige rodada %d/2"
                 % a_rodada), flush=True)
        for p in ((rel.get("relatorio") or {}).get("problemas") or [])[:10]:
            print("  [clipe %s] %s / %s: %s" % (p.get("clipe"), p.get("severidade"),
                  p.get("campo"), str(p.get("problema"))[:180]), flush=True)
        if a_rodada == 3:
            break
        mensagens = mensagens + [
            {"role": "assistant", "content": (cru or "")[:60000]},
            {"role": "user", "content": mensagem_correcao_auditoria(rel)},
        ]
        j = gerar(pieces, fcfg, mensagens)
        (EPISODIOS / "_ultima_geracao.json").write_text(
            json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        cru = j.get("cru") or ""
        ep = j["episodio"]
        ok, val, erros, av_clipe = avaliar(ep)
        (EPISODIOS / "_ultima_validacao.json").write_text(
            json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")
        if not ok or len(ep.get("shots") or []) != 6:
            lista = "\n".join("%d. %s" % (i + 1, e) for i, e in enumerate(erros[:14])) \
                or "- o JSON deve ter EXATAMENTE 6 objetos em shots (c01..c06), dur 10"
            # avisos que derrubam a nota de render (ex.: "alguem parece parado")
            # precisam entrar na re-correcao — so os erros nao bastam.
            extra = ""
            if av_clipe:
                extra = ("\n\nAVISOS QUE DERRUBAM O RENDER — corrija tambem:\n"
                         + "\n".join("- " + a for a in av_clipe[:8]))
            mensagens = mensagens + [
                {"role": "assistant", "content": (cru or "")[:60000]},
                {"role": "user", "content": (
                    "A correcao do auditor quebrou o contrato do validador. Devolva O "
                    "JSON COMPLETO corrigido, preservando as correcoes de causalidade/"
                    "fisica e resolvendo:\n" + lista + extra +
                    "\nLembre: em todo plano os DOIS corpos agem fisicamente (nunca "
                    "stays/waits/watches); som bucal moderado (2-5 de 6 clipes).")},
            ]
            j = gerar(pieces, fcfg, mensagens)
            (EPISODIOS / "_ultima_geracao.json").write_text(
                json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
            cru = j.get("cru") or ""
            ep = j["episodio"]
            ok, val, erros, av_clipe = avaliar(ep)
            (EPISODIOS / "_ultima_validacao.json").write_text(
                json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")
        if not ok or len(ep.get("shots") or []) != 6:
            _reset_gate("correcao do auditor nao passou no validador")
            raise SystemExit("XX a correcao do auditor nao passou no validador - "
                             "settings/smoke NAO foram gerados")
        episodio = ep

    if not aprovado:
        _reset_gate("auditoria reprovou apos 1 auditoria + 2 correcoes")
        aa = ((rel.get("relatorio") or {}).get("auditoria") or {}) if rel else {}
        raise SystemExit("XX auditoria nao aprovou (status=%s, causalidade=%s) - "
                         "settings/smoke NAO foram gerados"
                         % (aa.get("status"),
                            (aa.get("notas") or {}).get("causalidade")))

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
        destino.joinpath("auditoria_v6.json").write_text(
            json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
        print(">>> respostas brutas salvas: geracao_v6.json + validacao_v6.json + "
              "auditoria_v6.json", flush=True)

    st, cfgs = _post("/api/settings", {"episodio": episodio})
    if st != 201:
        raise SystemExit("XX settings falhou (HTTP %s): %s" % (st, str(cfgs)[:400]))
    print(">>> SETTINGS gerados (total %s s)" % cfgs.get("total_s"))

    a_final = (rel.get("relatorio") or {}).get("auditoria") or {}
    META.write_text(json.dumps({"slug": slug, "pasta": pasta, "tema": tema["tema"],
                                "resumo": tema["resumo"], "ideia": tema["ideia"],
                                "auditoria": {
                                    "status": a_final.get("status"),
                                    "nota_geral": a_final.get("nota_geral"),
                                    "causalidade": (a_final.get("notas") or {}).get(
                                        "causalidade"),
                                    "falhas_criticas": a_final.get("falhas_criticas"),
                                    "rodadas": a_rodada,
                                    "modelo": rel.get("modelo"),
                                }},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(">>> meta para a cadeia: %s" % META)
    g = _registra_gate(slug, rel)
    print(">>> GATE V6: %d/3 historias aprovadas consecutivas%s"
          % (g.get("consecutivas", 0),
             " - SMOKE LIBERADO" if g.get("consecutivas", 0) >= 3 else ""))
    print("\n>>> TESTE DO MOTOR OK — episódio válido (3 camadas) + auditoria Sol "
          "aprovada.")


if __name__ == "__main__":
    main()
