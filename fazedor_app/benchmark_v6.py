# -*- coding: utf-8 -*-
"""
benchmark_v6.py — Astra x Sol na V6 (criação + auditoria cruzada).

CINCO TAREFAS (mesmas para os dois modelos):
  1. criar uma história visualmente engraçada;
  2. resolver uma sequência com objetos persistentes;
  3. construir uma escalada de seis clipes;
  4. encontrar erros de causalidade em história propositalmente defeituosa;
  5. corrigir a história sem destruir a ideia original.

DEPOIS: auditoria cruzada (Astra cria → Sol audita; Sol cria → Astra audita).

CRITÉRIOS (pesos): criatividade 25% · causalidade 25% · continuidade 25% ·
obediência ao JSON 15% · eficiência/concisão 10%.

Uso:
  python benchmark_v6.py            # modo seco: mostra plano, tarefas e fixture, SEM chamadas
  python benchmark_v6.py --run      # executa (servidor ligado, chaves em config_secret.json)
  python benchmark_v6.py --run --modelos gpt-6.2-astra gpt-6.2-sol

AVISO: --run faz várias chamadas longas (5–15 min cada) e custa tokens.
"""
import argparse
import copy
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8756"
AR_MODELOS = ["gpt-6.2-astra", "gpt-6.2-sol"]
PESOS = {"criatividade": 0.25, "causalidade": 0.25, "continuidade": 0.25,
         "obediencia_json": 0.15, "eficiencia": 0.10}
SAIDA = Path(__file__).resolve().parent.parent / "BENCHMARK_V6_RESULTADO.json"

IDEIAS = {
    1: ("Contratados para tirar as cracas do casco de um navio encalhado na praia. "
        "TÉO inventa um equipamento medido com precisão; JUCA executa na marra. "
        "Cada tentativa cria um caos material novo."),
    2: ("Num galpão, uma escada tomba no terceiro clipe e fica atravessada no chão. "
        "Ela precisa continuar exatamente ali nos clipes seguintes, virar obstáculo "
        "de JUCA e só sair quando alguém a mover com uma ação visível."),
    3: ("Serviço de vedação num átrio: seis clipes de 10 s. Comece num objeto pequeno "
        "e escale para parede, piso e teto, com a mesma mecânica voltando com física "
        "diferente. Um único degrau de superfície, escalada acontecendo dentro dele."),
}

DEFECTOS_PLANTADOS = [
    {"clipe": 2, "campo": "estado_in", "descricao": "estado_in nao casa com estado_out do clipe 1"},
    {"clipe": 1, "campo": "non_diegetic_music", "descricao": "musica N/A (a V6 exige instrumental)"},
    {"clipe": 2, "campo": "causa", "descricao": "efeito sem causa visivel"},
    {"clipe": 3, "campo": "planos", "descricao": "clipe com um unico plano"},
]


def episodio_base():
    """Episódio V6 válido de 3 clipes, reaproveitado como gabarito/fixture."""
    b1 = ("TEO lifts the old bucket from the floor and sets it down beside the drain, "
          "while JUCA shoulders a steel pipe and walks past behind him, his boot "
          "splashing the thin puddle that already covers the tiles.")
    b2 = ("JUCA pushes the tipped bucket with his boot and it slides across the wet "
          "tiles, while TEO holds his tape measure over the spreading puddle and "
          "writes the number down on a small pad.")
    b3 = ("TEO hands the folded invoice to the client and bows slightly, while JUCA "
          "pushes the floating bucket away with one clog and adjusts his flat cap.")
    return {
        "titulo": "BALDE QUE VAZA", "logline": "Um balde vaza no corredor.",
        "setor": "residencial", "servico": "hidraulica", "cliente": "sindico",
        "mecanismo": "mediu errado", "degrau_final": "alaga o corredor",
        "callback_object": "balde", "set_historia": "SET: an empty tiled hallway, cool light.",
        "continuidade": ["TEO a esquerda", "JUCA a direita"],
        "assinatura": "nota fiscal entregue ao cliente mudo",
        "objetos_plantados": [{"objeto": "balde", "plantado_no_clipe": 1, "pago_no_clipe": 3}],
        "canon": "zeca_joca_v1", "premissa_simples": "trocar o balde",
        "solucao_errada": "medir o balde errado", "escalada": ["parede"],
        "payoff_visual": "o balde vaza e o corredor alaga", "otimismo_final": "aperto de maos",
        "shots": [
            {"n": 1, "dur": 10, "estagio": "LIGACAO",
             "estado_in": "empty hallway, dry floor", "estado_out": "bucket on the floor, water dripping",
             "planos": [{"t": "00:00.000", "texto": "Wide shot; the client in a suit stands at the doorway."},
                        {"t": "00:03.500", "texto": b1}],
             "gag": "o balde tomba e a agua escorre", "objeto_gag": "balde", "fisica": "tombar",
             "reacao": "TEO ergue as duas maos e alisa o bigode",
             "som": "metal clanks; water splashes; a low sigh",
             "overall_soundscape": "A metal bucket clanks on the tiles; water splashes; a low sigh",
             "non_diegetic_music": "A light pizzicato strings motif, playful and sparse",
             "causa": "balde velho", "efeito": "agua no chao", "payoff": "TEO ergue as maos", "escala": "parede"},
            {"n": 2, "dur": 10, "estagio": "PRIMEIRA_FALHA",
             "estado_in": "bucket on the floor, water dripping", "estado_out": "bucket tipped over, water spreading",
             "herda_de": "balde",
             "planos": [{"t": "00:00.000", "texto": "Close insert of the bucket rim, water pooling around it."},
                        {"t": "00:03.500", "texto": b2}],
             "gag": "o balde escorrega e derruba a agua", "objeto_gag": "balde", "fisica": "escorregar",
             "reacao": "JUCA apoia as maos nos joelhos e ajeita a boina",
             "som": "rubber sole squeaks; water sloshes; a short huff",
             "overall_soundscape": "A rubber sole squeaks on wet tiles; water sloshes; a short huff",
             "non_diegetic_music": "A muted clarinet phrase, curious and slow",
             "causa": "balde", "efeito": "agua se espalha", "payoff": "JUCA apoia as maos", "escala": "piso"},
            {"n": 3, "dur": 10, "estagio": "CLIMAX",
             "estado_in": "bucket tipped over, water spreading", "estado_out": "bucket tipped over, hallway flooded",
             "herda_de": "balde",
             "planos": [{"t": "00:00.000", "texto": "Wide shot of the flooded hallway; the client in a suit watches."},
                        {"t": "00:07.000", "texto": b3}],
             "gag": "o balde rola e a agua alaga tudo", "objeto_gag": "balde", "fisica": "rolar",
             "reacao": "TEO alisa o bigode e JUCA ajeita a boina",
             "som": "water laps the walls; paper rustles; a low whistle",
             "overall_soundscape": "Water laps the walls; paper rustles; a low whistle",
             "non_diegetic_music": "A small brass band stinger, bright and brief",
             "causa": "balde", "efeito": "corredor alagado", "payoff": "TEO entrega a nota fiscal", "escala": "teto"},
        ]}


def episodio_defeituoso():
    ep = episodio_base()
    ep["shots"][0]["non_diegetic_music"] = "N/A"
    ep["shots"][1]["estado_in"] = "dry corridor, nothing happened"
    ep["shots"][1]["causa"] = ""
    ep["shots"][2]["planos"] = ep["shots"][2]["planos"][:1]
    return ep


def post(caminho, obj, timeout=3600):
    req = urllib.request.Request(
        BASE + caminho, data=json.dumps(obj).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def get(caminho):
    with urllib.request.urlopen(BASE + caminho, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def api_para(modelo):
    f = get("/api/fcfg")
    return {"kind": "responses", "endpoint": f["ar_endpoint"], "model": modelo,
            "key": "", "max_tokens": 64000, "na_fallback": True}


def mensagens_criacao(v6, ideia):
    return [
        {"role": "system", "content": v6},
        {"role": "user", "content": "IDEIA DO USUÁRIO:\n" + ideia +
         "\n\nResponda com RESUMO (máx 8 linhas, PT) + um único bloco ```json``` "
         "no formato PROMPT_MESTRE_V6. Nada depois do JSON."},
    ]


def nota_geral(notas):
    return round(sum(PESOS[k] * float(notas.get(k, 0)) for k in PESOS), 2)


def detectados(relatorio):
    """Quantos dos defeitos plantados o auditor encontrou (por campo)."""
    problemas = relatorio.get("problemas") or []
    campos = {str(p.get("campo", "")).lower() for p in problemas if isinstance(p, dict)}
    return sum(1 for d in DEFECTOS_PLANTADOS if d["campo"].lower() in campos)


def executar(modelos):
    v6 = get("/api/pieces").get("v6") or ""
    if not v6:
        raise RuntimeError("/api/pieces não devolveu v6 — servidor desatualizado?")
    rel = {"modelos": modelos, "pesos": PESOS, "tarefas": {}, "cruzado": []}

    for modelo in modelos:
        print(f"\n=== {modelo} ===", flush=True)
        notas_modelo, detalhes = [], {}
        for tarefa in (1, 2, 3):
            t0 = time.time()
            j = post("/api/gerar", {"api": api_para(modelo),
                                    "messages": mensagens_criacao(v6, IDEIAS[tarefa])})
            ep = j.get("episodio")
            val = post("/api/validar", {"episodio": ep}) if isinstance(ep, dict) else {"erros": ["sem JSON"]}
            aud = post("/api/auditar", {"api": api_para(modelo), "episodio": ep,
                                        "modelo_criador": modelo, "mesmo_modelo": True})
            n = (aud.get("relatorio") or {}).get("auditoria", {}).get("notas", {})
            criatividade = float(n.get("acting_gags", 5))
            causalidade = float(n.get("causalidade", 5))
            continuidade = float(n.get("continuidade", 5))
            n_erros = len(val.get("erros") or [])
            obediencia = max(0.0, 10.0 - n_erros)
            tok = (j.get("uso") or {}).get("total_tokens") or 0
            eficiencia = max(0.0, 10.0 - tok / 12000.0)
            notas = {"criatividade": criatividade, "causalidade": causalidade,
                     "continuidade": continuidade, "obediencia_json": obediencia,
                     "eficiencia": eficiencia}
            notas_modelo.append(notas)
            detalhes[f"tarefa_{tarefa}"] = {"notas": notas, "geral": nota_geral(notas),
                                            "erros_validador": n_erros, "tokens": tok,
                                            "clipes": len((ep or {}).get("shots") or []),
                                            "s": round(time.time() - t0, 1)}
            print(f"  tarefa {tarefa}: nota {nota_geral(notas)} · {n_erros} erros · "
                  f"{tok} tokens · {detalhes[f'tarefa_{tarefa}']['s']}s", flush=True)

        # tarefa 4 — auditoria de historia defeituosa
        t0 = time.time()
        a4 = post("/api/auditar", {"api": api_para(modelo), "episodio": episodio_defeituoso(),
                                   "modelo_criador": "fixture", "mesmo_modelo": True})
        n4 = detectados(a4.get("relatorio") or {})
        print(f"  tarefa 4 (auditoria): {n4}/{len(DEFECTOS_PLANTADOS)} defeitos detectados", flush=True)
        detalhes["tarefa_4"] = {"defeitos_detectados": n4,
                                "total_defeitos": len(DEFECTOS_PLANTADOS),
                                "status": (a4.get("relatorio") or {}).get("auditoria", {}).get("status")}

        # tarefa 5 — correção localizada
        t0 = time.time()
        epd = episodio_defeituoso()
        corr = post("/api/gerar", {"api": api_para(modelo), "messages": [
            {"role": "system", "content": v6},
            {"role": "user", "content": "CORRIJA o JSON abaixo mantendo a ideia original. "
             "Devolva o JSON COMPLETO no formato PROMPT_MESTRE_V6.\n\n" +
             json.dumps(epd, ensure_ascii=False)}]})
        ep5 = corr.get("episodio")
        val5 = post("/api/validar", {"episodio": ep5}) if isinstance(ep5, dict) else {"erros": ["sem JSON"]}
        n_erros5 = len(val5.get("erros") or [])
        detalhes["tarefa_5"] = {"erros_apos_correcao": n_erros5,
                                "era": len(post("/api/validar", {"episodio": epd})["erros"]),
                                "s": round(time.time() - t0, 1)}
        print(f"  tarefa 5 (correcao): {detalhes['tarefa_5']['era']} -> {n_erros5} erros", flush=True)

        medias = {k: round(sum(m[k] for m in notas_modelo) / len(notas_modelo), 2) for k in PESOS}
        medias["deteccao_defeitos"] = round(n4 / len(DEFECTOS_PLANTADOS) * 10, 2)
        rel["tarefas"][modelo] = {"detalhes": detalhes, "medias": medias,
                                  "nota_final": nota_geral(medias)}

    # auditoria cruzada: cada modelo cria, o OUTRO audita
    for criador in modelos:
        auditor = next((m for m in AR_MODELOS if m != criador), None)
        if not auditor:
            continue
        j = post("/api/gerar", {"api": api_para(criador),
                                "messages": mensagens_criacao(v6, IDEIAS[1])})
        ep = j.get("episodio")
        if not isinstance(ep, dict):
            continue
        a = post("/api/auditar", {"api": api_para(auditor), "episodio": ep,
                                  "modelo_criador": criador})
        rel["cruzado"].append({"criador": criador, "auditor": auditor,
                               "status": (a.get("relatorio") or {}).get("auditoria", {}).get("status"),
                               "notas": (a.get("relatorio") or {}).get("auditoria", {}).get("notas"),
                               "problemas": len((a.get("relatorio") or {}).get("problemas") or [])})
        print(f"  cruzado: {criador} -> {auditor}: "
              f"{rel['cruzado'][-1]['status']} ({rel['cruzado'][-1]['problemas']} problemas)", flush=True)

    SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nRESULTADO:", json.dumps({m: rel["tarefas"][m]["nota_final"] for m in modelos},
                                    ensure_ascii=False), flush=True)
    print("arquivo:", SAIDA, flush=True)
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="executa as chamadas de API")
    ap.add_argument("--dry", action="store_true",
                    help="modo seco (padrao); nao chama API")
    ap.add_argument("--modelos", nargs="+", default=AR_MODELOS)
    a = ap.parse_args()
    if not a.run:
        print("MODO SECO — nenhuma chamada de API sera feita.\n")
        print("Tarefas:")
        for k, v in IDEIAS.items():
            print(f"  {k}. {v}")
        print("\nAuditores/modelos:", ", ".join(a.modelos))
        print("Defeitos plantados para a tarefa 4:")
        for d in DEFECTOS_PLANTADOS:
            print("  -", d["clipe"], d["campo"], ":", d["descricao"])
        print("\nPesos:", PESOS)
        print("\nPara executar: python benchmark_v6.py --run (servidor ligado; chamadas longas).")
        return
    executar(a.modelos)


if __name__ == "__main__":
    main()
