# -*- coding: utf-8 -*-
"""teste_canon.py — prova que o CÉREBRO DE COMÉDIA está no motor e no validador.

Roda sem GPU e sem rede:
    python teste_canon.py

Cobre:
  1. o canon (Zeca e Joca + causa→efeito→payoff) existe e está no prompt mestre;
  2. instrucoes_dossie() (AgentRouter) carrega o cérebro;
  3. reforcar_canon() injeta em qualquer provedor sem duplicar;
  4. o validador exige os campos novos quando o episódio declara canon;
  5. um clipe sem payoff é reprovado.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

import canon_comedia
import regras_v4
import fazedor_app


def check(cond, msg):
    print(("OK   " if cond else "FALHA ") + msg)
    if not cond:
        raise SystemExit(1)


# ── 1 · o canon existe e está no prompt mestre ──────────────────────────────
check(canon_comedia.VERSAO == "zeca_joca_v1", "versão do canon = zeca_joca_v1")
bloco = canon_comedia.BLOCO_MESTRE
check("ZECA E JOCA" in bloco, "bloco cita Zeca e Joca / Pat & Mat")
check("INCONGRU" in bloco and "ESCALADA" in bloco, "bloco traz a mecânica do riso")
check("CAUSA -> EFEITO -> PAYOFF" in bloco, "bloco traz a corrente causa→efeito→payoff")
check("REGISTRO DE OBJETOS" in bloco, "bloco traz o contrato anti-teleporte")
check("ORIGINALIDADE" in bloco, "bloco traz a cláusula de originalidade")
check("FICHA VISUAL IMUTÁVEL" in bloco, "bloco fixa a ficha visual nas âncoras")
check("NADA SE RESOLVE POR SORTE" in bloco, "bloco proíbe solução por sorte")
check("canon\": \"zeca_joca_v1" in bloco or "zeca_joca_v1" in bloco,
      "bloco declara o schema canon")
check(canon_comedia.MARCA in regras_v4.PROMPT_MESTRE_V5,
      "PROMPT_MESTRE_V5 contém o cérebro")
check(len(regras_v4.PROMPT_MESTRE_V5) > len(regras_v4.PROMPT_MESTRE_V4),
      "V5 é maior que V4 (bloco realmente anexado)")

# ── 2 · AgentRouter recebe o cérebro ────────────────────────────────────────
sist = fazedor_app.instrucoes_dossie()
check(canon_comedia.MARCA in sist, "instrucoes_dossie() (AgentRouter) contém o cérebro")

# ── 3 · reforco em qualquer provedor, sem duplicar ──────────────────────────
msgs = [{"role": "system", "content": "prompt do usuário"},
        {"role": "user", "content": "ideia"}]
uma = fazedor_app.reforcar_canon(msgs)
check(canon_comedia.MARCA in uma[0]["content"], "reforcar_canon anexa ao system existente")
duas = fazedor_app.reforcar_canon(uma)
check(duas[0]["content"].count(canon_comedia.MARCA) == 1,
      "reforcar_canon é idempotente (não duplica)")
sem_sys = fazedor_app.reforcar_canon([{"role": "user", "content": "ideia"}])
check(sem_sys[0]["role"] == "system" and canon_comedia.MARCA in sem_sys[0]["content"],
      "reforcar_canon cria system quando não existe")


# ── 4 · validador: canon declarado exige o arco completo ────────────────────
def ep_base():
    ei1 = "lisa wall, blank; the picture frame leans on the floor"
    eo1 = "a small nail is bent in the wall, the frame still on the floor"
    ei2 = eo1
    eo2 = "a crack runs up the wall from the bent nail, the frame tilted"
    ei3 = eo2
    eo3 = "the picture hangs crooked on the cracked wall; the two shake hands"
    return {
        "titulo": "TESTE CANON",
        "canon": "zeca_joca_v1",
        "premissa_simples": "pendurar um quadro na parede",
        "solucao_errada": "usar um prego maior que a parede aguenta",
        "escalada": ["objeto", "parede", "piso"],
        "payoff_visual": "o quadro pendurado torto na parede rachada",
        "otimismo_final": "eles apertam as mãos orgulhosos sob o quadro torto",
        "callback_object": "picture frame",
        "degrau_final": "a parede racha e o quadro fica torto",
        "objetos_plantados": [{"objeto": "picture frame", "plantado_no_clipe": 1,
                               "pago_no_clipe": 3}],
        "continuidade": ["TÉO à esquerda", "JUCA à direita"],
        "assinatura": "nota fiscal entregue ao cliente mudo",
        "set_historia": "SET: interior of a small workshop, brick walls, wet floor",
        "shots": [
            {"n": 1, "dur": 10, "estagio": "LIGACAO",
             "estado_in": ei1, "estado_out": eo1,
             "planos": [{"t": "00:00.000", "texto": "Close insert of the bent nail in TEO's fingers."},
                        {"t": "00:03.500", "texto": "TEO taps the nail; the plaster cracks."}],
             "gag": "o prego entorta e racha a parede", "objeto_gag": "picture frame",
             "fisica": "dobrar",
             "reacao": "TEO alisa o bigode e apoia a mão no joelho; snort",
             "som": "martelo bate; parede estala; respiração; snort",
             "overall_soundscape": "hammer taps; plaster cracks; TEO snorts",
             "non_diegetic_music": "N/A",
             "causa": "o prego torto escolhido por TEO",
             "efeito": "a parede racha", "payoff": "TEO alisa o bigode",
             "escala": "objeto"},
            {"n": 2, "dur": 10, "estagio": "ESCALADA",
             "estado_in": ei2, "estado_out": eo2,
             "planos": [{"t": "00:00.000", "texto": "Insert of the crack running up the wall."},
                        {"t": "00:03.500", "texto": "JUCA pushes the frame; the wall bulges."}],
             "gag": "a parede cede e empurra o quadro", "objeto_gag": "picture frame",
             "fisica": "tombar",
             "reacao": "JUCA ajeita a boina e encolhe os ombros; sigh",
             "som": "parede estala; gesso cai; quadro range; sigh",
             "overall_soundscape": "plaster crumbles; frame creaks; JUCA sighs",
             "non_diegetic_music": "N/A",
             "herda_de": "picture frame",
             "causa": "o prego torto do clipe anterior", "efeito": "a parede cede",
             "payoff": "JUCA ajeita a boina", "escala": "parede"},
            {"n": 3, "dur": 10, "estagio": "CLIMAX",
             "estado_in": ei3, "estado_out": eo3,
             "planos": [{"t": "00:00.000", "texto": "Insert of the crooked picture frame."},
                        {"t": "00:03.500", "texto": "The frame settles crooked; they shake hands."}],
             "gag": "o quadro fica pendurado torto e eles comemoram", "objeto_gag": "picture frame",
             "fisica": "rolar",
             "reacao": "TÉO e JUCA apertam as mãos e endireitam a coluna; snort",
             "som": "quadro range; gesso cai; mãos se apertam; snort",
             "overall_soundscape": "frame creaks; plaster falls; a firm handshake slaps; snort",
             "non_diegetic_music": "N/A",
             "herda_de": "picture frame",
             "causa": "a parede rachada do clipe anterior", "efeito": "o quadro fica torto",
             "payoff": "eles apertam as mãos orgulhosos", "escala": "piso"}
        ],
    }


r = regras_v4.validar_montagem(ep_base())
canon_erros = [e for e in r["erros"] if "CANON" in e]
check(not canon_erros, "episódio canon completo não gera erro de CANON (%d)" % len(canon_erros))
check(any("cérebro de comédia" in c for c in r["checks"]),
      "validador registra o check do cérebro de comédia")

quebrado = ep_base()
quebrado["shots"][1]["payoff"] = ""
r2 = regras_v4.validar_montagem(quebrado)
check(any("CANON [2]: campo 'payoff' ausente" in e for e in r2["erros"]),
      "clipe sem payoff é reprovado pelo canon")

legado = ep_base()
legado.pop("canon")
r3 = regras_v4.validar_montagem(legado)
check(any("CANON: episódio sem" in a for a in r3["avisos"]),
      "episódio legado recebe aviso (não quebra o passado)")

print("\n>>> CÉREBRO DE COMÉDIA OK — injetado no prompt, no AgentRouter, em todos os "
      "provedores e no validador.")
